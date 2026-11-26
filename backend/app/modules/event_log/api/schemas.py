from datetime import datetime
from typing import Any, Optional

from app.core.dto import ResponseModel
from app.core.events import EventCategory


class EventLogEntryResponse(ResponseModel):
    id: int
    category: EventCategory
    event_type: str
    occurred_at: datetime
    actor_id: Optional[int]
    actor_login: Optional[str]
    actor_name: Optional[str]
    ip_address: Optional[str]
    payload: dict[str, Any]


class EventLogPageResponse(ResponseModel):
    items: list[EventLogEntryResponse]
    total: int


class NotificationsResponse(ResponseModel):
    items: list[EventLogEntryResponse]
    total: int
    unread_count: int


class OutboxRetryResponse(ResponseModel):
    retried: int
