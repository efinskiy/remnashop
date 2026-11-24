from contextlib import suppress

from loguru import logger
from remnapy import RemnawaveSDK

from app.core.actor import Actor
from app.core.db.uow import UnitOfWork
from app.core.enums import SubscriptionStatus
from app.core.ports import EventPublisher
from app.core.usecase import UseCase
from app.core.utils.time import datetime_now
from app.modules.settings import SettingsRepository
from app.modules.subscriptions.events import SubscriptionExpiryDisabledEvent
from app.modules.subscriptions.expiry_disable import disable_due
from app.modules.subscriptions.lifecycle import SubscriptionLifecycleService
from app.modules.subscriptions.panel import drop_connections, panel_user_gone
from app.modules.subscriptions.repository import SubscriptionRepository


class DisableExpiredSubscriptionUseCase(UseCase[int, None]):
    """Switches off the panel user of a subscription expired past the rule's days."""

    # system-only: the expiry disable sweep
    required_permission = None

    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        settings_repository: SettingsRepository,
        lifecycle_service: SubscriptionLifecycleService,
        remnawave_sdk: RemnawaveSDK,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
    ) -> None:
        self._subscription_repository = subscription_repository
        self._settings_repository = settings_repository
        self._lifecycle_service = lifecycle_service
        self._remnawave_sdk = remnawave_sdk
        self._uow = uow
        self._event_publisher = event_publisher

    async def _execute(self, actor: Actor, data: int) -> None:
        now = datetime_now()
        async with self._uow:
            settings = await self._settings_repository.get_grace_settings()
            subscription = await self._subscription_repository.get_by_id(data)
        if not disable_due(subscription, settings, now):
            return

        users = self._remnawave_sdk.users
        try:
            panel_user = await users.disable_user(subscription.remnawave_user_id)
        except Exception as error:
            if not panel_user_gone(error):
                raise
            # its deletion webhook settles the row
            logger.warning(f"Panel user of expired subscription '{data}' is gone, not disabling")
            return
        await drop_connections(self._remnawave_sdk, subscription.remnawave_user_id)

        async with self._uow:
            current = await self._subscription_repository.get_by_id_for_update(data)
            if (
                current.status is SubscriptionStatus.EXPIRED
                and current.expire_at == subscription.expire_at
                and current.grace_until is None
            ):
                await self._lifecycle_service.sync_status(
                    data, SubscriptionStatus(panel_user.status)
                )
                await self._subscription_repository.set_expiry_disabled_at(data, now)
                await self._event_publisher.publish(
                    SubscriptionExpiryDisabledEvent(subscription_id=data, user_id=current.user_id)
                )
                logger.info(f"Disabled subscription '{data}' expired past the rule's days")
                return
            # renewed, changed, put in grace or switched by an admin while the panel call ran
            owner = await self._subscription_repository.find_by_remnawave_user_id(
                subscription.remnawave_user_id
            )
        if owner is None or owner.status in (
            SubscriptionStatus.DISABLED,
            SubscriptionStatus.DELETED,
        ):
            return
        with suppress(Exception):
            await users.enable_user(owner.remnawave_user_id)
            logger.info(f"Subscription '{data}' moved on while being disabled, enabled it back")
