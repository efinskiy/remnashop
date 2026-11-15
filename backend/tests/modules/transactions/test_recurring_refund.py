from decimal import Decimal

import pytest
from sqlalchemy import update

from app.core.db.models import RecurringPayment, Transaction
from app.core.enums import Currency, Locale, PurchaseChannel, PurchaseType, TransactionStatus
from app.core.utils.time import datetime_now
from app.modules.transactions.recurring_policy import recurring_policy
from app.modules.transactions.recurring_repository import RecurringPaymentRepository
from app.modules.transactions.recurring_terms import build_recurring_terms
from tests.fakes.recurring import ShippedRecurringTermsTexts
from tests.modules.transactions.test_handle_payment_webhook import (
    _order,
    _refunded,
    _report,
    _ReportingGateway,
    purchase_dispatch,
)
from tests.modules.transactions.test_usecases import _seed_subscription

__all__ = ["purchase_dispatch"]


async def _mandate(session, uow, subscription_repository, order) -> tuple[int, int]:
    subscription_id = await _seed_subscription(
        subscription_repository,
        user_id=order.user_id,
        remnawave_user_id=830_000 + order.id,
        plan_id=order.plan_id,
    )
    terms = await build_recurring_terms(
        texts=ShippedRecurringTermsTexts(),
        policy=recurring_policy({}),
        user_id=order.user_id,
        plan_id=order.plan_id,
        target_subscription_id=subscription_id,
        purchase_type=PurchaseType.RENEW,
        initial_amount=Decimal("500"),
        amount_limit=Decimal("500"),
        currency=Currency.RUB,
        duration_days=30,
        locale=Locale.RU,
    )
    repository = RecurringPaymentRepository(session)
    async with uow:
        consent_id = await repository.record_consent(
            terms, channel=PurchaseChannel.BOT, telegram_id=None
        )
        await session.execute(
            update(Transaction)
            .where(Transaction.id == order.id)
            .values(target_subscription_id=subscription_id, is_recurring=True)
        )
        session.add(
            RecurringPayment(
                subscription_id=subscription_id,
                enabled=True,
                consent_id=consent_id,
                payment_method_id="pm-saved",
                source_transaction_id=order.id,
                next_attempt_at=datetime_now(),
            )
        )
    return subscription_id, consent_id


@pytest.mark.parametrize(
    "amount", [pytest.param("500.00", id="full"), pytest.param("100.00", id="partial")]
)
async def test_refund_of_a_renewal_disables_auto_renewal(
    amount,
    session,
    transaction_repository,
    subscription_repository,
    user_repository,
    uow,
    user_id,
    plan_id,
    gateway_repository,
    purchase_dispatch,
) -> None:  # type: ignore[no-untyped-def]
    order = await _order(
        transaction_repository, uow, user_id, plan_id, status=TransactionStatus.PAID
    )
    subscription_id, consent_id = await _mandate(session, uow, subscription_repository, order)
    await _report(
        _ReportingGateway(_refunded(amount, "RUB")),
        transaction_repository=transaction_repository,
        user_repository=user_repository,
        uow=uow,
        gateway_repository=gateway_repository,
        purchase_dispatch=purchase_dispatch,
    )
    repository = RecurringPaymentRepository(session)
    mandate = await repository.get(subscription_id)
    assert mandate is not None and not mandate.enabled
    assert mandate.last_error == "refunded"
    assert await repository.consent_terms(consent_id) is None
    assert subscription_id not in await repository.list_due(
        datetime_now(), due_before=datetime_now().replace(year=2100), limit=100
    )
