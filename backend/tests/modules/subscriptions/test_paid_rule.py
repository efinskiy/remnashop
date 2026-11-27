from datetime import timedelta
from decimal import Decimal
from typing import Optional

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.uow import UnitOfWork
from app.core.enums import (
    Currency,
    DiscountSource,
    PaymentGatewayType,
    PurchaseChannel,
    PurchaseType,
    TransactionStatus,
)
from app.core.utils.time import datetime_now
from app.modules.subscriptions.repository import SubscriptionRepository
from app.modules.subscriptions.stats_repository import SubscriptionStatsRepository
from app.modules.transactions.dto import CreateTransactionDto
from app.modules.transactions.repository import TransactionRepository
from app.modules.users.repository import UserRepository
from tests.modules.subscriptions.factories import create_subscription, make_plan_snapshot


@pytest.mark.parametrize(
    ("price_paid", "is_trial", "order", "expected"),
    [
        (Decimal("100"), False, None, True),
        # a free plan, a promocode or bonus grant, a panel import
        (Decimal("0"), False, None, False),
        # imported, then renewed for money: the renewal leaves the snapshot's 0
        (Decimal("0"), False, (TransactionStatus.PAID, Decimal("100"), False), True),
        (Decimal("0"), False, (TransactionStatus.PAID, Decimal("0"), False), False),
        (Decimal("0"), False, (TransactionStatus.PAID, Decimal("100"), True), False),
        (Decimal("0"), False, (TransactionStatus.REFUNDED, Decimal("100"), False), False),
        (Decimal("100"), True, None, False),
    ],
)
async def test_paid_subscription_rule(
    session: AsyncSession,
    uow: UnitOfWork,
    subscription_repository: SubscriptionRepository,
    user_repository: UserRepository,
    price_paid: Decimal,
    is_trial: bool,
    order: Optional[tuple[TransactionStatus, Decimal, bool]],
    expected: bool,
) -> None:
    stats = SubscriptionStatsRepository(session)
    before = await stats.count_paying()
    subscription = await create_subscription(
        subscription_repository,
        user_repository,
        telegram_id=880_001,
        remnawave_user_id=880_001,
        is_trial=is_trial,
        price_paid=price_paid,
    )
    if order is not None:
        status, final_price, is_test = order
        transactions = TransactionRepository(session)
        created = await transactions.create(
            CreateTransactionDto(
                channel=PurchaseChannel.CABINET,
                user_id=subscription.user_id,
                plan_id=None,
                plan_snapshot=make_plan_snapshot(),
                duration_days=30,
                currency=Currency.RUB,
                purchase_type=PurchaseType.RENEW,
                target_subscription_id=subscription.id,
                gateway_type=PaymentGatewayType.YOOKASSA,
                base_price=final_price,
                discount_percent=0,
                discount_source=DiscountSource.NONE,
                final_price=final_price,
                anchor_base_price=final_price,
                anchor_final_price=final_price,
                customer_email=None,
                idempotency_key="paid-rule",
                expires_at=datetime_now() + timedelta(minutes=30),
                is_test=is_test,
            )
        )
        await transactions.mark_status(created.id, status)
        await transactions.mark_fulfilled(created.id, subscription.id)

    assert await stats.count_paying() - before == int(expected)
    assert [
        row.is_paid for row in await stats.list_live() if row.user_id == subscription.user_id
    ] == [expected]
    assert (
        await subscription_repository.has_paid_subscription_before(subscription.user_id) is expected
    )
