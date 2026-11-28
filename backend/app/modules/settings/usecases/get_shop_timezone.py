from app.core.actor import Actor
from app.core.db.uow import UnitOfWork
from app.core.security.permissions import Permission
from app.core.usecase import UseCase
from app.modules.settings.dto import ShopTimezoneDto
from app.modules.settings.repository import SettingsRepository


class GetShopTimezoneUseCase(UseCase[None, ShopTimezoneDto]):
    # every admin's dashboard counts the shop's days, whatever else they may see
    required_permission = Permission.PUBLIC

    def __init__(self, settings_repository: SettingsRepository, uow: UnitOfWork) -> None:
        self._settings_repository = settings_repository
        self._uow = uow

    async def _execute(self, actor: Actor, data: None) -> ShopTimezoneDto:
        async with self._uow:
            settings = await self._settings_repository.get_shop_settings()
        return ShopTimezoneDto(timezone=settings.timezone)
