from dataclasses import dataclass
from typing import ClassVar

from app.core.events import BaseEvent, EventCategory, UserEvent
from app.modules.users import CabinetSignInMethod


@dataclass(frozen=True, kw_only=True)
class EmailCodeAttemptsExhaustedEvent(BaseEvent):
    category: ClassVar[EventCategory] = EventCategory.AUTH
    email_hash: str


@dataclass(frozen=True, kw_only=True)
class CabinetNewDeviceSignInEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.AUTH
    browser: str


@dataclass(frozen=True, kw_only=True)
class CabinetSignedInEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.AUTH
    method: CabinetSignInMethod
