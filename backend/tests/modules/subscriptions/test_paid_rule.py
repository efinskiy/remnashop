from decimal import Decimal
from typing import Optional

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
    assert (
        await subscription_repository.has_paid_subscription_before(subscription.user_id) is expected
    )
