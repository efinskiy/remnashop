from dataclasses import dataclass
from typing import ClassVar

from app.core.events import EventCategory, SystemEvent


@dataclass(frozen=True, kw_only=True)
class OutboxEntryPoisonedEvent(SystemEvent):
    category: ClassVar[EventCategory] = EventCategory.INFRASTRUCTURE
    outbox_id: int
    failed_event: str
    error: str
