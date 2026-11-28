from datetime import timedelta
from typing import Final

from loguru import logger

from app.core.actor import Actor
from app.core.db.uow import UnitOfWork
from app.core.usecase import UseCase
from app.core.utils.time import datetime_now
from app.modules.settings import SettingsRepository
from app.modules.subscriptions.expiry_disable import CLAIM_STALE_AFTER
from app.modules.subscriptions.repository import SubscriptionRepository
from app.modules.subscriptions.usecases.disable_expired_subscription import (
    DisableExpiredSubscriptionUseCase,
)
from app.modules.subscriptions.usecases.warn_of_expiry_disable import WarnOfExpiryDisableUseCase

_BATCH: Final[int] = 100


class SweepExpiryDisableUseCase(UseCase[None, None]):
    """Warns of and carries out the expiry rule's switch-off."""

    # system-only: the cron
    required_permission = None

    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        settings_repository: SettingsRepository,
        uow: UnitOfWork,
        warn_of_expiry_disable_use_case: WarnOfExpiryDisableUseCase,
        disable_expired_subscription_use_case: DisableExpiredSubscriptionUseCase,
    ) -> None:
        self._subscription_repository = subscription_repository
        self._settings_repository = settings_repository
        self._uow = uow
        self._warn_of_expiry_disable_use_case = warn_of_expiry_disable_use_case
        self._disable_expired_subscription_use_case = disable_expired_subscription_use_case

    async def _execute(self, actor: Actor, data: None) -> None:
        now = datetime_now()
        async with self._uow:
            settings = await self._settings_repository.get_grace_settings()
            if not settings.expiry_disable_enabled:
                return
            # lapsed this long ago is due for the switch-off
            due_before = now - timedelta(days=settings.expiry_disable_after_days)
            warning = (
                await self._subscription_repository.list_expiry_disable_warn_due(
                    due_before + timedelta(days=settings.expiry_disable_warn_days),
                    due_before,
                    _BATCH,
                )
                if settings.expiry_disable_warn_days
                else []
            )
            due = await self._subscription_repository.list_expiry_disable_due(
                due_before, now - CLAIM_STALE_AFTER, _BATCH
            )
        for subscription in warning:
            try:
                await self._warn_of_expiry_disable_use_case.system(subscription.id)
            except Exception:
                logger.exception(f"Failed to warn of disabling subscription '{subscription.id}'")
        for subscription in due:
            try:
                await self._disable_expired_subscription_use_case.system(subscription.id)
            except Exception:
                logger.exception(f"Failed to disable expired subscription '{subscription.id}'")
