from dataclasses import dataclass
from typing import ClassVar, Literal, Optional

from app.core.events import ActorEvent, EventCategory, SystemEvent
from app.modules.blacklist.dto import BlacklistKind


@dataclass(frozen=True, kw_only=True)
class BlacklistEntryChangedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.SETTINGS
    action: Literal["create", "delete"]
    kind: BlacklistKind
    value: str


@dataclass(frozen=True, kw_only=True)
class BlacklistReconciledEvent(SystemEvent):
    category: ClassVar[EventCategory] = EventCategory.USER
    blocked_user_ids: list[int]


@dataclass(frozen=True, kw_only=True)
class BlacklistSourceChangedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.SETTINGS
    action: Literal["create", "delete", "disable", "enable", "sync"]
    source_id: Optional[int] = None
