from dataclasses import dataclass
from typing import ClassVar, Literal, Optional

from app.core.events import ActorEvent, EventCategory


@dataclass(frozen=True, kw_only=True)
class ApiTokenChangedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.ADMIN_MANAGEMENT
    action: Literal["create", "delete"]
    token_id: int
    # set on "create"
    name: Optional[str] = None
