import time
from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import Any, Awaitable, Callable, ClassVar, Final, Optional

from aiogram import BaseMiddleware, Router
from aiogram.types import Message, TelegramObject
from aiogram.types import User as AiogramUser
from loguru import logger


# https://docs.aiogram.dev/en/latest/api/types/update.html
class MiddlewareEventType(StrEnum):
    AIOGD_UPDATE = auto()  # aiogram-dialog
    UPDATE = auto()
    MESSAGE = auto()
    EDITED_MESSAGE = auto()
    CHANNEL_POST = auto()
    EDITED_CHANNEL_POST = auto()
    BUSINESS_CONNECTION = auto()
    BUSINESS_MESSAGE = auto()
    EDITED_BUSINESS_MESSAGE = auto()
    DELETED_BUSINESS_MESSAGES = auto()
    MESSAGE_REACTION = auto()
    MESSAGE_REACTION_COUNT = auto()
    INLINE_QUERY = auto()
    CHOSEN_INLINE_RESULT = auto()
    CALLBACK_QUERY = auto()
    SHIPPING_QUERY = auto()
    PRE_CHECKOUT_QUERY = auto()
    PURCHASED_PAID_MEDIA = auto()
    POLL = auto()
    POLL_ANSWER = auto()
    MY_CHAT_MEMBER = auto()
    CHAT_MEMBER = auto()
    CHAT_JOIN_REQUEST = auto()
    CHAT_BOOST = auto()
    REMOVED_CHAT_BOOST = auto()
    ERROR = auto()


DEFAULT_UPDATE_TYPES: Final[list[MiddlewareEventType]] = [
    MiddlewareEventType.MESSAGE,
    MiddlewareEventType.CALLBACK_QUERY,
]


# a charged customer must reach the payment handler whatever gate they fail
def is_successful_payment(event: TelegramObject) -> bool:
    return isinstance(event, Message) and event.successful_payment is not None


class EventTypedMiddleware(BaseMiddleware, ABC):
    __event_types__: ClassVar[list[MiddlewareEventType]] = DEFAULT_UPDATE_TYPES

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start = time.perf_counter()
        result = await self.middleware_logic(handler, event, data)
        logger.debug(
            f"Middleware '{self.__class__.__name__}' executed in {time.perf_counter() - start:.4f}s"
        )
        return result

    def setup_outer(self, router: Router) -> None:
        for event_type in self.__event_types__:
            router.observers[event_type].outer_middleware(self)

    def setup_inner(self, router: Router) -> None:
        for event_type in self.__event_types__:
            router.observers[event_type].middleware(self)

    @abstractmethod
    async def middleware_logic(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any: ...

    def _get_aiogram_user(self, data: dict[str, Any]) -> Optional[AiogramUser]:
        user = data.get("event_from_user")
        return user if isinstance(user, AiogramUser) else None
