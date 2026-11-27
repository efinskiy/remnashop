from dataclasses import dataclass
from typing import ClassVar, Literal, Optional

from app.core.events import ActorEvent, EventCategory, SystemEvent


@dataclass(frozen=True, kw_only=True)
class BroadcastChangedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.BROADCAST
    action: Literal[
        "add_email_image",
        "cancel",
        "create",
        "delete",
        "delete_media",
        "duplicate",
        "recall",
        "retry",
        "schedule",
        "set_media",
        "update",
    ]
    broadcast_id: int
    # set on a duplicate: the broadcast it was copied from
    source_broadcast_id: Optional[int] = None
    # set on a schedule, ISO 8601
    scheduled_at: Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class BroadcastStartedEvent(SystemEvent):
    category: ClassVar[EventCategory] = EventCategory.BROADCAST
    broadcast_id: int
    total: int
    promocode_dropped: bool


@dataclass(frozen=True, kw_only=True)
class BroadcastCompletedEvent(SystemEvent):
    category: ClassVar[EventCategory] = EventCategory.BROADCAST
    broadcast_id: int
    sent: int
    failed: int
    blocked: int


@dataclass(frozen=True, kw_only=True)
class BroadcastFailedEvent(SystemEvent):
    category: ClassVar[EventCategory] = EventCategory.BROADCAST
    broadcast_id: int
    error: str
