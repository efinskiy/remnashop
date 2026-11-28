from typing import Any, Awaitable, Callable, ClassVar

from aiogram.types import TelegramObject

from app.core.constants import CONTAINER_KEY
from app.modules.settings import GetShopSettingsUseCase
from app.telegram.i18n import use_shop_zone
from app.telegram.middlewares.base import EventTypedMiddleware, MiddlewareEventType


class ShopZoneMiddleware(EventTypedMiddleware):
    """Dates the bot writes for this update are the shop's (settings cached per process)."""

    __event_types__: ClassVar[list[MiddlewareEventType]] = [
        MiddlewareEventType.MESSAGE,
        MiddlewareEventType.CALLBACK_QUERY,
        MiddlewareEventType.AIOGD_UPDATE,
    ]

    async def middleware_logic(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        get_shop_settings = await data[CONTAINER_KEY].get(GetShopSettingsUseCase)
        use_shop_zone((await get_shop_settings.system()).zone)
        return await handler(event, data)
