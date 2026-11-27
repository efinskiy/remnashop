from dataclasses import dataclass
from typing import ClassVar, Literal, Optional

from app.core.enums import Locale
from app.core.events import ActorEvent, EventCategory


@dataclass(frozen=True, kw_only=True)
class LocaleChangedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.SETTINGS
    action: Literal["activate", "deactivate", "set_default"]
    locale: Locale


@dataclass(frozen=True, kw_only=True)
class TranslationChangedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.SETTINGS
    action: Literal["import", "reset", "reset_all", "update"]
    locale: Optional[Locale] = None
    key: Optional[str] = None
