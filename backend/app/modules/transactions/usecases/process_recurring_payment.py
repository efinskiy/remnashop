from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

import httpx
from loguru import logger

from app.core.actor import Actor
from app.core.config import AppConfig
from app.core.db.uow import UnitOfWork
from app.core.enums import (
    Currency,
    Locale,
    PaymentGatewayType,
    PurchaseType,
    SubscriptionStatus,
    TransactionStatus,
)
from app.core.exceptions import AppError
from app.core.usecase import UseCase
from app.core.utils.time import datetime_now
from app.modules.gateways import GatewayRepository
from app.modules.settings import SettingsRepository
from app.modules.subscriptions import (
    PlanSnapshot,
    SubscriptionDto,
    SubscriptionRepository,
)
from app.modules.transactions.checkout_pricing import CheckoutPricer
from app.modules.transactions.dto import (
    CreateTransactionDto,
    ProcessRecurringPaymentDto,
    TransactionDto,
)
from app.modules.transactions.gateways.yookassa import YooKassaGateway
from app.modules.transactions.ports import PaymentTexts
from app.modules.transactions.recurring_dto import RecurringPaymentDto
from app.modules.transactions.recurring_lifecycle import RecurringLifecycle
from app.modules.transactions.recurring_policy import (
    POLICY_RECHECK_DELAY,
    SAFE_REPOST_WINDOW,
    RecurringReason,
    recurring_reason,
)
from app.modules.transactions.recurring_poller import RecurringPoller, pending_expired
from app.modules.transactions.recurring_repository import RecurringPaymentRepository
from app.modules.transactions.recurring_submission import RecurringSubmission, submit_recurring
from app.modules.transactions.recurring_terms import RecurringTerms
from app.modules.transactions.repository import TransactionRepository
from app.modules.users import UserDto, UserRepository


class ProcessRecurringPaymentUseCase(UseCase[ProcessRecurringPaymentDto, None]):
    required_permission = None

    def __init__(
        self,
        recurring_repository: RecurringPaymentRepository,
        recurring_lifecycle: RecurringLifecycle,
        recurring_poller: RecurringPoller,
        transaction_repository: TransactionRepository,
        subscription_repository: SubscriptionRepository,
        user_repository: UserRepository,
        gateway_repository: GatewayRepository,
        settings_repository: SettingsRepository,
        pricer: CheckoutPricer,
        uow: UnitOfWork,
        config: AppConfig,
        payment_texts: PaymentTexts,
    ) -> None:
        self._recurring = recurring_repository
        self._lifecycle = recurring_lifecycle
        self._poller = recurring_poller
        self._transactions = transaction_repository
        self._subscriptions = subscription_repository
        self._users = user_repository
        self._gateways = gateway_repository
        self._settings = settings_repository
        self._pricer = pricer
        self._uow = uow
        self._config = config
        self._payment_texts = payment_texts

    async def _execute(self, actor: Actor, data: ProcessRecurringPaymentDto) -> None:
        await self._run_one(data.subscription_id)

    async def _run_one(self, subscription_id: int) -> None:
        try:
            await self._process(subscription_id)
        except Exception as error:
            await self._uow.rollback()
            kind = (
                f"HTTP {error.response.status_code}"
                if isinstance(error, httpx.HTTPStatusError)
                else type(error).__name__
            )
            logger.error(f"Recurring payment for subscription '{subscription_id}': {kind}")
            async with self._uow:
                mandate = await self._recurring.get(subscription_id)
                order = (
                    await self._transactions.get_by_id(mandate.pending_transaction_id)
                    if mandate and mandate.pending_transaction_id
                    else None
                )
                terms = await self._recurring.consent_terms(mandate.consent_id) if mandate else None
                if (
                    mandate
                    and order
                    and order.external_payment_id
                    and pending_expired(mandate, order, terms)
                ):
                    await self._lifecycle.pause(subscription_id, "pending_timeout")
                else:
                    merchant = isinstance(
                        error, httpx.HTTPStatusError
                    ) and error.response.status_code in {401, 403}
                    await self._defer(
                        subscription_id,
                        "merchant_unavailable" if merchant else "provider_unavailable",
                    )

    async def _defer(self, subscription_id: int, error: Optional[str] = None) -> None:
        mandate = await self._recurring.get(subscription_id)
        terms = await self._recurring.consent_terms(mandate.consent_id) if mandate else None
        minutes = terms.retry_minutes if terms else self._config.recurring.retry_minutes
        reason = recurring_reason(error or (mandate.last_error if mandate else None))
        delay = (
            POLICY_RECHECK_DELAY
            if reason is RecurringReason.PENDING_TIMEOUT
            else timedelta(minutes=minutes)
        )
        await self._lifecycle.defer(subscription_id, datetime_now() + delay, error)

    async def _enabled(self) -> bool:
        gateway = await self._gateways.get_by_type(PaymentGatewayType.YOOKASSA)
        access = await self._settings.get_access_settings()
        return bool(
            access.payments_enabled
            and gateway.is_active
            and gateway.is_configured
            and gateway.flags.get("recurring_enabled", False)
        )

    async def _process(self, subscription_id: int) -> None:
        async with self._uow:
            mandate = await self._recurring.get(subscription_id)
            if mandate is None:
                return
        if mandate.pending_transaction_id is None:
            reason = recurring_reason(mandate.last_error)
            if not mandate.enabled or (reason is not None and not reason.policy.allows_debit):
                return
            await self._reserve(mandate)
        await self._charge_or_poll(subscription_id)

    async def _reservation_gateway(
        self, mandate: RecurringPaymentDto, customer_email: Optional[str]
    ) -> Optional[YooKassaGateway]:
        gateway = await self._poller.gateway()
        if mandate.shop_id != gateway.settings.shop_id or not mandate.payment_method_id:
            await self._lifecycle.pause(mandate.subscription_id, "shop_changed")
            return None
        if gateway.settings.vat_code is not None and not customer_email:
            await self._lifecycle.pause(mandate.subscription_id, "customer_email_required")
            return None
        return gateway

    async def _has_consent(
        self, mandate: RecurringPaymentDto, order: TransactionDto, amount: Decimal
    ) -> bool:
        terms = await self._recurring.consent_terms(mandate.consent_id)
        if terms is None:
            await self._lifecycle.disable(mandate.subscription_id, "consent_required")
            return False
        authorized = bool(
            terms
            and terms.covers(
                user_id=order.user_id,
                plan_id=order.plan_snapshot.plan_id,
                amount=amount,
                duration_days=order.duration_days,
                currency=order.currency,
            )
        )
        if not authorized:
            await self._lifecycle.pause(mandate.subscription_id, "consent_required")
        return authorized

    async def _reservation_available(self, mandate: RecurringPaymentDto) -> bool:
        async with self._uow:
            subscription = await self._subscriptions.get_by_id(mandate.subscription_id)
            terms = await self._recurring.consent_terms(mandate.consent_id)
            if subscription.status in {SubscriptionStatus.DELETED, SubscriptionStatus.DISABLED}:
                await self._lifecycle.close_for_plan_change(subscription.id)
                return False
            if terms and subscription.expire_at < datetime_now() - timedelta(
                hours=terms.max_overdue_hours
            ):
                await self._lifecycle.disable(
                    subscription.id, RecurringReason.RENEWAL_WINDOW_EXPIRED
                )
                return False
            return True

    async def _reserve(self, mandate: RecurringPaymentDto) -> None:
        if not await self._reservation_available(mandate):
            return
        async with self._uow:
            if not mandate.enabled or not await self._enabled():
                await self._defer(mandate.subscription_id, "gateway_disabled")
                return
            if await self._recurring.has_manual_waiting(mandate.subscription_id):
                await self._defer(mandate.subscription_id)
                return
            source = (
                await self._transactions.get_by_id(mandate.source_transaction_id)
                if mandate.source_transaction_id is not None
                else None
            )
            subscription = await self._subscriptions.get_by_id(mandate.subscription_id)
            user = await self._users.find_by_id(subscription.user_id)
        if (
            source is None
            or source.status is not TransactionStatus.PAID
            or user is None
            or user.deleted_at is not None
            or user.is_blocked
        ):
            async with self._uow:
                await self._lifecycle.disable(mandate.subscription_id, "subscription_unavailable")
            return
        try:
            async with self._uow:
                plan, user = await self._pricer.load_purchasable_plan(
                    user.id, source.plan_snapshot.plan_id, None, subscription.id
                )
            user = await self._pricer.drop_dead_promocode_discounts(user)
            # A one-shot discount is reserved by interactive checkouts, never by a timer.
            quote = await self._pricer.quote(
                plan,
                source.duration_days,
                Currency.RUB,
                user.model_copy(update={"purchase_discount": 0}),
            )
        except AppError:
            async with self._uow:
                await self._lifecycle.pause(mandate.subscription_id, "plan_unavailable")
            return

        async with self._uow:
            current = await self._recurring.get(subscription.id, for_update=True)
            terms = await self._reservation_terms(current, source, subscription.id)
            if terms is None or current is None:
                return
            shop = await self._settings.get_shop_settings()
            customer_email = shop.payment_email or user.email or source.customer_email
            gateway = await self._reservation_gateway(current, customer_email)
            if gateway is None:
                return
            vat_code = gateway.settings.vat_code
            subscription = await self._subscriptions.get_by_id_for_update(subscription.id)
            now = datetime_now()
            new_snapshot = PlanSnapshot.from_plan(
                plan,
                price_paid=quote.final_price,
                currency=Currency.RUB,
                duration_days=source.duration_days,
            )
            if not await self._valid_renewal(
                source, subscription, new_snapshot, quote.final_price, terms
            ):
                return
            if not await self._cycle_due(current, subscription.expire_at, terms):
                return
            order = await self._transactions.create(
                CreateTransactionDto(
                    user_id=user.id,
                    plan_id=plan.id,
                    plan_snapshot=new_snapshot,
                    duration_days=source.duration_days,
                    currency=Currency.RUB,
                    purchase_type=PurchaseType.RENEW,
                    channel=source.channel,
                    target_subscription_id=subscription.id,
                    gateway_type=PaymentGatewayType.YOOKASSA,
                    base_price=quote.base_price,
                    discount_percent=quote.discount_percent,
                    discount_source=quote.discount_source,
                    plan_discount_percent=quote.plan_discount_percent,
                    final_price=quote.final_price,
                    anchor_base_price=quote.anchor_base_price,
                    anchor_final_price=quote.anchor_final_price,
                    customer_email=customer_email,
                    idempotency_key=uuid4().hex,
                    expires_at=now + SAFE_REPOST_WINDOW,
                    recurring_consent=True,
                    recurring_consent_id=current.consent_id,
                    is_recurring=True,
                    yookassa_receipt_vat_code=int(vat_code) if vat_code is not None else None,
                )
            )
            await self._lifecycle.set_pending(
                subscription.id, order.id, expire_at=subscription.expire_at
            )
        logger.info(f"Reserved recurring order '{order.id}' for subscription '{subscription.id}'")

    async def _valid_renewal(
        self,
        source: TransactionDto,
        subscription: SubscriptionDto,
        new_snapshot: PlanSnapshot,
        price: Decimal,
        terms: RecurringTerms,
    ) -> bool:
        now = datetime_now()
        if subscription.expire_at < now - timedelta(hours=terms.max_overdue_hours):
            await self._lifecycle.disable(subscription.id, RecurringReason.RENEWAL_WINDOW_EXPIRED)
            return False
        if (
            subscription.status
            not in {
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.EXPIRED,
                SubscriptionStatus.LIMITED,
            }
            or subscription.is_trial
            or subscription.plan_snapshot.plan_id != source.plan_id
            or source.plan_snapshot.terms_differ(subscription.plan_snapshot)
            or subscription.plan_snapshot.terms_differ(new_snapshot)
        ):
            await self._lifecycle.close_for_plan_change(subscription.id)
            return False
        if price <= 0 or price > source.base_price:
            await self._lifecycle.pause(subscription.id, "price_changed")
            return False
        return True

    async def _reservation_terms(
        self, mandate: Optional[RecurringPaymentDto], source: TransactionDto, subscription_id: int
    ) -> Optional[RecurringTerms]:
        if mandate is None or not mandate.enabled or mandate.pending_transaction_id is not None:
            return None
        reason = recurring_reason(mandate.last_error)
        if reason and not reason.policy.allows_debit:
            return None
        if mandate.source_transaction_id != source.id or not await self._enabled():
            await self._defer(subscription_id)
            return None
        if not await self._has_consent(mandate, source, source.base_price):
            return None
        return await self._recurring.consent_terms(mandate.consent_id)

    async def _cycle_due(
        self, mandate: RecurringPaymentDto, expire_at: datetime, terms: RecurringTerms
    ) -> bool:
        now = datetime_now()
        scheduled = expire_at - timedelta(minutes=terms.lead_minutes)
        if now < scheduled:
            if now >= expire_at - timedelta(minutes=self._config.recurring.notice_lead_minutes):
                await self._lifecycle.notify_upcoming(
                    mandate.subscription_id, expire_at, terms, scheduled
                )
            await self._lifecycle.defer(mandate.subscription_id, scheduled)
            return False
        if mandate.first_failure_at is not None:
            deadlines = [
                value
                for value in (mandate.bank_retry_at, mandate.next_attempt_at)
                if value is not None
            ]
            deadline = max(deadlines) if deadlines else None
            if deadline is not None and now < deadline:
                await self._lifecycle.defer(mandate.subscription_id, deadline)
                return False
        await self._lifecycle.notify_upcoming(mandate.subscription_id, expire_at, terms, scheduled)
        return True

    async def _pending_context(
        self, subscription_id: int
    ) -> Optional[tuple[RecurringPaymentDto, TransactionDto, YooKassaGateway]]:
        async with self._uow:
            current = await self._recurring.get(subscription_id)
            if current is None or current.pending_transaction_id is None:
                return None
            order = await self._transactions.get_by_id_for_update(current.pending_transaction_id)
            mandate = await self._recurring.get(subscription_id, for_update=True)
            if mandate is None or mandate.pending_transaction_id != order.id:
                return None
            if order.status is TransactionStatus.PAID:
                await self._defer(subscription_id)
                return None
            terms = await self._recurring.consent_terms(mandate.consent_id)
            gateway = await self._poller.gateway()
            if mandate.shop_id != gateway.settings.shop_id:
                await self._lifecycle.pause(
                    subscription_id,
                    "pending_timeout"
                    if order.external_payment_id and pending_expired(mandate, order, terms)
                    else "shop_changed",
                )
                await self._lifecycle.cancel_unsent(subscription_id, order.id)
                return None
            await self._defer(subscription_id)
            if order.external_payment_id is None and order.status is TransactionStatus.PENDING:
                if (
                    not mandate.enabled
                    or not mandate.payment_method_id
                    or not await self._enabled()
                    or await self._recurring.has_manual_waiting(subscription_id)
                ):
                    await self._lifecycle.cancel_unsent(subscription_id, order.id)
                    return None
        return mandate, order, gateway

    async def _charge_or_poll(self, subscription_id: int) -> None:
        async with self._uow:
            if await self._lifecycle.retire_pending(subscription_id):
                return
        context = await self._pending_context(subscription_id)
        if context is None:
            return
        _, order, gateway = context
        if order.status is not TransactionStatus.PENDING:
            if order.external_payment_id is not None:
                await self._poller.poll(subscription_id, order, gateway)
            return
        if order.external_payment_id is None:
            await self._charge(subscription_id, order)
            async with self._uow:
                order = await self._transactions.get_by_id(order.id)
        if order.external_payment_id is not None:
            await self._poller.poll(subscription_id, order, gateway)

    async def _submission_context(
        self,
        subscription_id: int,
        order: TransactionDto,
    ) -> Optional[tuple[TransactionDto, RecurringPaymentDto, RecurringTerms, YooKassaGateway]]:
        order = await self._transactions.get_by_id_for_update(order.id)
        if order.status is not TransactionStatus.PENDING or order.external_payment_id is not None:
            return None
        mandate = await self._recurring.get(subscription_id, for_update=True)
        if mandate is None or mandate.pending_transaction_id != order.id:
            return None
        if not mandate.enabled or not mandate.payment_method_id or not await self._enabled():
            await self._lifecycle.cancel_unsent(subscription_id, order.id)
            return None
        if await self._recurring.has_manual_waiting(subscription_id):
            await self._defer(subscription_id)
            return None
        if not await self._has_consent(mandate, order, order.final_price):
            await self._lifecycle.cancel_unsent(subscription_id, order.id)
            return None
        terms = await self._recurring.consent_terms(mandate.consent_id)
        if terms is None:
            return None
        gateway = await self._poller.gateway()
        if mandate.shop_id != gateway.settings.shop_id:
            await self._lifecycle.pause(subscription_id, "shop_changed")
            await self._lifecycle.cancel_unsent(subscription_id, order.id)
            return None
        subscription = await self._subscriptions.get_by_id(subscription_id)
        if await self._cycle_superseded(mandate, subscription):
            await self._lifecycle.cancel_unsent(subscription_id, order.id)
            return None
        user = await self._users.find_by_id(order.user_id)
        if self._subscription_unavailable(user, subscription, order, terms):
            reason = (
                RecurringReason.RENEWAL_WINDOW_EXPIRED
                if subscription.expire_at
                < datetime_now() - timedelta(hours=terms.max_overdue_hours)
                else RecurringReason.SUBSCRIPTION_UNAVAILABLE
            )
            await self._lifecycle.disable(subscription_id, reason)
            await self._lifecycle.cancel_unsent(subscription_id, order.id)
            return None
        return order, mandate, terms, gateway

    async def _submit_if_authorized(
        self,
        subscription_id: int,
        order: TransactionDto,
    ) -> Optional[tuple[RecurringPaymentDto, RecurringTerms, RecurringSubmission]]:
        async with self._uow:
            context = await self._submission_context(subscription_id, order)
            if context is None:
                return None
            order, mandate, terms, gateway = context
            unsubmitted = mandate.submitted_at is None
            submitted_at = await self._recurring.mark_submitted(subscription_id)
        # intent is committed before the request: a killed worker must not turn a
        # possibly charged key into an unsent order
        async with self._uow:
            context = await self._submission_context(subscription_id, order)
            if context is None:
                await self._abandon_submission(subscription_id, order, unsubmitted, submitted_at)
                return None
            order, mandate, terms, gateway = context
            first_attempt = unsubmitted and mandate.submitted_at == submitted_at
            text = await self._payment_texts.describe(order, Locale.RU)
        # no transaction or row lock while the provider answers; a withdrawal landing
        # now stops the next cycle, this already-sent payment may still complete
        result = await submit_recurring(
            gateway, order, text, mandate.payment_method_id or "", first_attempt=first_attempt
        )
        async with self._uow:
            current = await self._transactions.get_by_id_for_update(order.id)
            latest = await self._recurring.get(subscription_id, for_update=True)
            if (
                latest is not None
                and latest.pending_transaction_id == order.id
                and latest.submitted_at == mandate.submitted_at
                and current.status is TransactionStatus.PENDING
            ):
                await self._persist_submission(subscription_id, current, latest, terms, result)
        return mandate, terms, result

    async def _abandon_submission(
        self,
        subscription_id: int,
        order: TransactionDto,
        first_attempt: bool,
        submitted_at: datetime,
    ) -> None:
        if not first_attempt:
            return
        current = await self._transactions.get_by_id_for_update(order.id)
        mandate = await self._recurring.get(subscription_id, for_update=True)
        if (
            mandate
            and mandate.pending_transaction_id == order.id
            and mandate.submitted_at == submitted_at
            and current.status is TransactionStatus.PENDING
            and current.external_payment_id is None
        ):
            await self._recurring.clear_submission(subscription_id)
            await self._lifecycle.cancel_unsent(subscription_id, order.id)

    async def _charge(
        self,
        subscription_id: int,
        order: TransactionDto,
    ) -> None:
        await self._submit_if_authorized(subscription_id, order)

    async def _persist_submission(
        self,
        subscription_id: int,
        order: TransactionDto,
        mandate: RecurringPaymentDto,
        terms: RecurringTerms,
        result: RecurringSubmission,
    ) -> None:
        # The caller owns the order and current mandate until this entire outcome commits.
        if result.outcome == "ambiguous":
            await self._defer(
                subscription_id, result.reason or RecurringReason.PROVIDER_UNAVAILABLE
            )
            return
        if result.outcome == "accepted":
            moved = await self._transactions.mark_status_if(
                order.id,
                TransactionStatus.PENDING,
                current=frozenset({TransactionStatus.PENDING}),
                external_payment_id=result.payment_id,
            )
            if moved:
                await self._lifecycle.clear_error(subscription_id)
            return
        moved = await self._transactions.mark_status_if(
            order.id, TransactionStatus.FAILED, current=frozenset({TransactionStatus.PENDING})
        )
        if not moved:
            return
        if result.outcome in {"merchant", "configuration"}:
            await self._lifecycle.release_pending(
                subscription_id,
                order.id,
                reason=result.reason or RecurringReason.MERCHANT_UNAVAILABLE,
                retry_minutes=terms.retry_minutes,
            )
        else:
            await self._lifecycle.fail_pending(
                subscription_id,
                result.reason or RecurringReason.PAYMENT_METHOD_RESTRICTED,
                transaction_id=order.id,
                permanent=True,
            )

    async def _cycle_superseded(
        self, mandate: RecurringPaymentDto, subscription: SubscriptionDto
    ) -> bool:
        return mandate.cycle_expire_at is None or subscription.expire_at > mandate.cycle_expire_at

    @staticmethod
    def _subscription_unavailable(
        user: Optional[UserDto],
        subscription: SubscriptionDto,
        order: TransactionDto,
        terms: RecurringTerms,
    ) -> bool:
        return (
            user is None
            or user.is_blocked
            or user.deleted_at is not None
            or subscription.expire_at < datetime_now() - timedelta(hours=terms.max_overdue_hours)
            or subscription.status in {SubscriptionStatus.DELETED, SubscriptionStatus.DISABLED}
            or subscription.plan_snapshot.terms_differ(order.plan_snapshot)
            or subscription.plan_snapshot.plan_id != order.plan_id
        )
