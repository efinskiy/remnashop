import importlib
from decimal import Decimal
from typing import Final

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.models.event_log import EventLogEntry
from app.core.db.models.event_outbox import EventOutboxEntry
from app.core.db.models.subscription import Subscription
from app.core.events import EventCategory
from app.core.utils.time import datetime_now
from app.modules.subscriptions.repository import SubscriptionRepository
from app.modules.users.repository import UserRepository
from tests.modules.subscriptions.factories import create_subscription

_MIGRATION: Final = importlib.import_module(
    "app.core.db.migrations.versions.1046_subscriptions_replaced_paid"
)


async def test_backfill_flags_every_row_a_paid_one_was_changed_into(
    session: AsyncSession,
    subscription_repository: SubscriptionRepository,
    user_repository: UserRepository,
) -> None:
    async def sub(n: int, price: str) -> int:
        row = await create_subscription(
            subscription_repository,
            user_repository,
            telegram_id=890_000 + n,
            remnawave_user_id=890_000 + n,
            price_paid=Decimal(price),
        )
        return row.id

    paid, middle, last = await sub(1, "300"), await sub(2, "0"), await sub(3, "0")
    free, free_next = await sub(4, "0"), await sub(5, "0")
    queued, queued_next = await sub(6, "300"), await sub(7, "0")

    def change(event_type: str, old: int, new: int) -> dict:
        return {
            "category": EventCategory.SUBSCRIPTION,
            "event_type": event_type,
            "occurred_at": datetime_now(),
            "payload": {"subscription_id": new, "previous_subscription_id": old},
        }

    session.add_all(
        [
            EventLogEntry(**change("SubscriptionChangedEvent", paid, middle)),
            # a change of the changed row: the flag passes on through it
            EventLogEntry(**change("SubscriptionPlanChangedByAdminEvent", middle, last)),
            EventLogEntry(**change("SubscriptionChangedEvent", free, free_next)),
            # not moved to the log yet
            EventOutboxEntry(**change("SubscriptionChangedEvent", queued, queued_next)),
        ]
    )
    await session.flush()

    await session.execute(text(_MIGRATION._BACKFILL))

    rows = await session.execute(select(Subscription.id, Subscription.replaced_paid))
    flags = dict(rows.tuples().all())
    assert {i: flags[i] for i in (paid, middle, last, free, free_next, queued, queued_next)} == {
        paid: False,
        middle: True,
        last: True,
        free: False,
        free_next: False,
        queued: False,
        queued_next: True,
    }
