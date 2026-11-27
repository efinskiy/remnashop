import datetime

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppConfig
from app.core.config.build import BuildConfig
from app.core.db.models import EventOutboxEntry
from app.core.db.uow import UnitOfWork
from app.core.enums import Locale, Role
from app.core.event_bus import EventBus
from app.core.events import MASKED_IP, EventCategory
from app.core.exceptions import PermissionDeniedError
from app.modules.event_log.dto import EventLogEntryDto, ListEventLogDto
from app.modules.event_log.outbox_repository import EventOutboxRepository
from app.modules.event_log.repository import EventLogRepository
from app.modules.event_log.usecases import (
    ListEventLogUseCase,
    ProcessOutboxEntryUseCase,
    PruneOutboxUseCase,
    RetryPoisonedOutboxUseCase,
    SweepOutboxUseCase,
)
from app.modules.event_log.usecases.retry_poisoned_outbox import RETRY_WITHIN
from app.modules.users.dto import CreateUserDto, UserDto
from app.modules.users.repository import UserRepository

OWNER = UserDto(id=1, login="owner", name="owner", role=Role.OWNER, language=Locale.EN)
REGULAR_ADMIN = UserDto(id=2, login="admin", name="admin", role=Role.ADMIN, language=Locale.EN)
GRANTED_ADMIN = UserDto(
    id=3,
    login="admin2",
    name="admin2",
    role=Role.ADMIN,
    language=Locale.EN,
    permission_grants=["EVENT_LOG_VIEW"],
)


async def test_owner_can_list_event_log(
    event_log_repository: EventLogRepository,
    uow: UnitOfWork,
) -> None:
    await event_log_repository.create(
        EventLogEntryDto(
            category=EventCategory.AUTH,
            event_type="LoginSucceededEvent",
            occurred_at=datetime.datetime.now(datetime.timezone.utc),
            payload={},
        )
    )

    use_case = ListEventLogUseCase(event_log_repository, uow)
    items, total = await use_case(OWNER, ListEventLogDto())

    assert total == 1
    assert len(items) == 1


async def test_regular_admin_without_grant_cannot_list_event_log(
    event_log_repository: EventLogRepository,
    uow: UnitOfWork,
) -> None:
    use_case = ListEventLogUseCase(event_log_repository, uow)

    with pytest.raises(PermissionDeniedError):
        await use_case(REGULAR_ADMIN, ListEventLogDto())


async def test_admin_with_grant_can_list_event_log(
    event_log_repository: EventLogRepository,
    uow: UnitOfWork,
) -> None:
    use_case = ListEventLogUseCase(event_log_repository, uow)

    items, total = await use_case(GRANTED_ADMIN, ListEventLogDto())

    assert total == 0
    assert items == []


async def test_list_event_log_passes_filters_through(
    event_log_repository: EventLogRepository,
    uow: UnitOfWork,
) -> None:
    await event_log_repository.create(
        EventLogEntryDto(
            category=EventCategory.ADMIN_MANAGEMENT,
            event_type="AdminCreatedEvent",
            occurred_at=datetime.datetime.now(datetime.timezone.utc),
            payload={},
        )
    )
    await event_log_repository.create(
        EventLogEntryDto(
            category=EventCategory.AUTH,
            event_type="LoginSucceededEvent",
            occurred_at=datetime.datetime.now(datetime.timezone.utc),
            payload={},
        )
    )

    use_case = ListEventLogUseCase(event_log_repository, uow)
    items, total = await use_case(OWNER, ListEventLogDto(category=EventCategory.ADMIN_MANAGEMENT))

    assert total == 1
    assert items[0].event_type == "AdminCreatedEvent"


async def test_list_event_log_masks_staff_ips_from_admins(
    event_log_repository: EventLogRepository,
    user_repository: UserRepository,
    uow: UnitOfWork,
) -> None:
    # was a customer when acting, staff now
    promoted = await user_repository.create(
        CreateUserDto(name="promoted", login="promoted", role=Role.ADMIN)
    )
    customer = await user_repository.create(CreateUserDto(name="customer"))
    for user in (promoted, customer):
        await event_log_repository.create(
            EventLogEntryDto(
                category=EventCategory.USER,
                event_type="CabinetSignedInEvent",
                occurred_at=datetime.datetime.now(datetime.timezone.utc),
                actor_id=user.id,
                ip_address=f"203.0.113.{user.id % 250}",
                payload={"user": {"id": user.id, "role": "USER"}},
            )
        )
    use_case = ListEventLogUseCase(event_log_repository, uow)

    admin_view, _ = await use_case(GRANTED_ADMIN, ListEventLogDto())
    owner_view, _ = await use_case(OWNER, ListEventLogDto())

    by_actor = {item.actor_id: item.ip_address for item in admin_view}
    assert by_actor[promoted.id] == MASKED_IP
    assert by_actor[customer.id] != MASKED_IP
    assert MASKED_IP not in {item.ip_address for item in owner_view}


def _poisoned(occurred_at: datetime.datetime) -> EventOutboxEntry:
    return EventOutboxEntry(
        category=EventCategory.AUTH,
        event_type="LoginSucceededEvent",
        occurred_at=occurred_at,
        payload={},
        attempts=5,
    )


async def test_retry_on_start_processes_recent_poisoned_entries_once_per_build(
    session: AsyncSession,
    uow: UnitOfWork,
    redis: Redis,
    config: AppConfig,
    event_log_repository: EventLogRepository,
) -> None:
    now = datetime.datetime.now(datetime.timezone.utc)
    recent = _poisoned(now - datetime.timedelta(days=1))
    old = _poisoned(now - RETRY_WITHIN - datetime.timedelta(hours=1))
    session.add_all([recent, old])
    await session.flush()
    outbox = EventOutboxRepository(session)
    sweep = SweepOutboxUseCase(
        outbox, ProcessOutboxEntryUseCase(outbox, event_log_repository, EventBus(), uow), uow
    )

    def use_case(commit: str) -> RetryPoisonedOutboxUseCase:
        built = config.model_copy(update={"build": BuildConfig(commit=commit)})
        return RetryPoisonedOutboxUseCase(built, redis, outbox, sweep, uow)

    assert await use_case("aaa").system() == 1
    await session.refresh(recent)
    await session.refresh(old)
    assert recent.processed_at is not None
    assert (old.processed_at, old.attempts) == (None, 5)

    again = _poisoned(now)
    session.add(again)
    await session.flush()
    # a restart of the same build leaves them alone, a new build retries
    assert await use_case("aaa").system() == 0
    assert await use_case("bbb").system() == 1


async def test_prune_drops_poisoned_entries_past_the_retention(
    session: AsyncSession, uow: UnitOfWork
) -> None:
    now = datetime.datetime.now(datetime.timezone.utc)
    old = _poisoned(now - datetime.timedelta(days=15))
    recent = _poisoned(now - datetime.timedelta(days=13))
    session.add_all([old, recent])
    await session.flush()
    outbox = EventOutboxRepository(session)

    await PruneOutboxUseCase(outbox, uow).system()

    assert (await outbox.get_poisoned_stats()).unprocessed_count == 1
