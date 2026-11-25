from app.core.actor import Actor
from app.core.db.uow import UnitOfWork
from app.core.ports import EventPublisher
from app.core.usecase import UseCase
from app.core.utils.time import datetime_now
from app.modules.settings import SettingsRepository
from app.modules.subscriptions.eligibility import subscription_owner
from app.modules.subscriptions.events import SubscriptionExpiryDisableWarningEvent
from app.modules.subscriptions.expiry_disable import disable_at, warning_due
from app.modules.subscriptions.repository import SubscriptionRepository
from app.modules.users import UserRepository


class WarnOfExpiryDisableUseCase(UseCase[int, None]):
    """Tells the customer when the expiry rule will switch their subscription off."""

    # system-only: the expiry disable sweep
    required_permission = None

    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        settings_repository: SettingsRepository,
        user_repository: UserRepository,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
    ) -> None:
        self._subscription_repository = subscription_repository
        self._settings_repository = settings_repository
        self._user_repository = user_repository
        self._uow = uow
        self._event_publisher = event_publisher

    async def _execute(self, actor: Actor, data: int) -> None:
        now = datetime_now()
        async with self._uow:
            settings = await self._settings_repository.get_grace_settings()
            subscription = await self._subscription_repository.get_by_id_for_update(data)
            if not warning_due(subscription, settings, now):
                return
            await self._subscription_repository.mark_expiry_disable_warned(data, now)
            await self._event_publisher.publish(
                SubscriptionExpiryDisableWarningEvent(
                    user=await subscription_owner(self._user_repository, subscription),
                    subscription_id=data,
                    disable_at=disable_at(subscription, settings).isoformat(),
                )
            )
