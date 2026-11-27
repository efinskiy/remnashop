from datetime import timedelta
from typing import Final

from loguru import logger
from redis.asyncio import Redis

from app.core.actor import Actor
from app.core.config import AppConfig
from app.core.constants import REDIS_KEY_PREFIX
from app.core.db.uow import UnitOfWork
from app.core.usecase import UseCase
from app.core.utils.time import datetime_now
from app.modules.event_log.outbox_repository import EventOutboxRepository
from app.modules.event_log.usecases.sweep_outbox import SweepOutboxUseCase

_LAST_BUILD_KEY: Final[str] = f"{REDIS_KEY_PREFIX}outbox:retried_build"
# older events would reach customers as stale notices
RETRY_WITHIN: Final[timedelta] = timedelta(days=3)


class RetryPoisonedOutboxUseCase(UseCase[None, int]):
    """Run on worker start: a new build may carry the fix for what poisoned the rows,
    or be the worker catching up with an api that published a newer event shape."""

    required_permission = None

    def __init__(
        self,
        config: AppConfig,
        redis: Redis,
        outbox_repository: EventOutboxRepository,
        sweep_use_case: SweepOutboxUseCase,
        uow: UnitOfWork,
    ) -> None:
        self._config = config
        self._redis = redis
        self._outbox_repository = outbox_repository
        self._sweep_use_case = sweep_use_case
        self._uow = uow

    async def _execute(self, actor: Actor, data: None) -> int:
        build = self._config.build.commit or self._config.build.version
        # atomic swap: of several worker processes starting together, one retries;
        # a restart of the same build retries nothing
        if await self._redis.set(_LAST_BUILD_KEY, build, get=True) == build:
            return 0
        async with self._uow:
            retried = await self._outbox_repository.reset_poisoned(
                occurred_after=datetime_now() - RETRY_WITHIN
            )
        if retried:
            logger.info(f"Build '{build}': retrying {retried} poisoned outbox entries")
            # at once, not on the next cron tick: until processed, the old rows read as a
            # stuck queue
            await self._sweep_use_case.system()
        return retried
