from decimal import Decimal
from typing import Optional

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.models.credit_segment import CreditSegment
from app.core.enums import CreditSegmentKind, Currency
from app.modules.subscriptions.credit_segment_repository import CreditSegmentRepository
from app.modules.subscriptions.dto import CreateCreditSegmentDto
from app.modules.subscriptions.repository import SubscriptionRepository
from app.modules.subscriptions.stats_repository import SubscriptionStatsRepository
from app.modules.users.repository import UserRepository
from tests.modules.subscriptions.factories import create_subscription


@pytest.mark.parametrize(
    ("price_paid", "is_trial", "segment", "expected"),
    [
        (Decimal("100"), False, None, True),
        # a free plan, a promocode or bonus grant, a panel import
        (Decimal("0"), False, None, False),
        (Decimal("0"), False, (CreditSegmentKind.BONUS, Decimal("0")), False),
        # imported, then renewed for money: the renewal leaves the snapshot's 0
        (Decimal("0"), False, (CreditSegmentKind.PURCHASE, Decimal("100")), True),
        # a plan change paid by credit, or made by an admin, writes 0 to the new row
        (Decimal("0"), False, (CreditSegmentKind.CARRIED, Decimal("300")), True),
        (Decimal("100"), True, None, False),
    ],
)
async def test_paid_subscription_rule(
    session: AsyncSession,
    subscription_repository: SubscriptionRepository,
    user_repository: UserRepository,
    price_paid: Decimal,
    is_trial: bool,
    segment: Optional[tuple[CreditSegmentKind, Decimal]],
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
    if segment is not None:
        kind, paid = segment
        await CreditSegmentRepository(session).create(
            CreateCreditSegmentDto(
                subscription_id=subscription.id,
                kind=kind,
                paid=paid,
                currency=Currency.RUB,
                seconds=30 * 86400,
                ends_at=subscription.expire_at,
            )
        )

    assert await stats.count_paying() - before == int(expected)
    live = [row.is_paid for row in await stats.list_live() if row.user_id == subscription.user_id]
    assert live == [expected]
    assert await subscription_repository.has_paid_subscription(subscription.user_id) is expected


async def test_a_sale_counts_when_its_segment_says_zero(
    session: AsyncSession,
    subscription_repository: SubscriptionRepository,
    user_repository: UserRepository,
) -> None:
    # migration 1027 wrote a term renewed free after it lapsed with paid 0
    subscription = await create_subscription(
        subscription_repository,
        user_repository,
        telegram_id=880_002,
        remnawave_user_id=880_002,
        price_paid=Decimal("300"),
    )
    await session.execute(
        update(CreditSegment)
        .where(CreditSegment.subscription_id == subscription.id)
        .values(paid=Decimal("0"))
    )

    live = await SubscriptionStatsRepository(session).list_live()
    assert [row.is_paid for row in live if row.user_id == subscription.user_id] == [True]


async def test_a_paid_renewal_of_a_free_subscription_is_no_purchase(
    session: AsyncSession,
    subscription_repository: SubscriptionRepository,
    user_repository: UserRepository,
) -> None:
    # FIRST_PAYMENT rewards a NEW purchase only: the renewal earned nothing, so the
    # purchase after it is still the first one
    free = await create_subscription(
        subscription_repository, user_repository, telegram_id=880_003, remnawave_user_id=880_003
    )
    await CreditSegmentRepository(session).create(
        CreateCreditSegmentDto(
            subscription_id=free.id,
            kind=CreditSegmentKind.PURCHASE,
            paid=Decimal("300"),
            currency=Currency.RUB,
            seconds=30 * 86400,
            ends_at=free.expire_at,
        )
    )
    later = free.id + 1_000

    assert await subscription_repository.has_paid_subscription(free.user_id)
    assert not await subscription_repository.has_bought_subscription_before(free.user_id, later)


async def test_a_sale_before_makes_a_purchase_not_the_first(
    subscription_repository: SubscriptionRepository,
    user_repository: UserRepository,
) -> None:
    sold = await create_subscription(
        subscription_repository,
        user_repository,
        telegram_id=880_004,
        remnawave_user_id=880_004,
        price_paid=Decimal("300"),
    )

    assert await subscription_repository.has_bought_subscription_before(sold.user_id, sold.id + 1)
    assert not await subscription_repository.has_bought_subscription_before(sold.user_id, sold.id)
