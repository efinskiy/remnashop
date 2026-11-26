from functools import partial

from loguru import logger

from app.core.actor import Actor
from app.core.db.uow import UnitOfWork
from app.core.ports import EventPublisher, OutboxEntryDispatch
from app.core.security.permissions import Permission
from app.core.usecase import UseCase
from app.modules.event_log.dto import RetryPoisonedOutboxDto
from app.modules.event_log.events import OutboxRetriedEvent
from app.modules.event_log.outbox_repository import EventOutboxRepository


class RetryPoisonedOutboxUseCase(UseCase[RetryPoisonedOutboxDto, int]):
    required_permission = Permission.OUTBOX_RETRY

    def __init__(
        self,
        outbox_repository: EventOutboxRepository,
        outbox_entry_dispatch: OutboxEntryDispatch,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
    ) -> None:
        self._outbox_repository = outbox_repository
        self._outbox_entry_dispatch = outbox_entry_dispatch
        self._uow = uow
        self._event_publisher = event_publisher

    async def _execute(self, actor: Actor, data: RetryPoisonedOutboxDto) -> int:
        async with self._uow:
            entry_ids = await self._outbox_repository.reset_poisoned()
            if not entry_ids:
                return 0
            await self._event_publisher.publish(
                OutboxRetriedEvent(actor=actor, count=len(entry_ids), ip_address=data.client_ip)
            )
            # kicked now, not left to the sweep: until processed, the old rows read as a stuck queue
            for entry_id in entry_ids:
                await self._uow.after_commit(
                    partial(self._outbox_entry_dispatch.kiq, outbox_id=entry_id)
                )
        logger.info(f"{actor.log} Retried {len(entry_ids)} poisoned outbox entries")
        return len(entry_ids)
