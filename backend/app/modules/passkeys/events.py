from dataclasses import dataclass
from typing import ClassVar, Literal, Optional

from app.core.events import BaseEvent, EventCategory, UserEvent


@dataclass(frozen=True, kw_only=True)
class PasskeyLoginSucceededEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.AUTH
    credential_name: Optional[str]


@dataclass(frozen=True, kw_only=True)
class PasskeyLoginFailedEvent(BaseEvent):
    category: ClassVar[EventCategory] = EventCategory.AUTH
    # None when the credential wasn't recognised, the usual failure
    credential_id: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class PasskeyChangedEvent(UserEvent):
    category: ClassVar[EventCategory] = EventCategory.AUTH
    action: Literal["create", "delete", "rename"]
    credential_name: Optional[str]
