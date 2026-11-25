from datetime import datetime

from app.core.dto import ResponseModel


class CustomerFeedItemResponse(ResponseModel):
    id: int
    event_type: str
    title: str
    body: str
    url: str
    created_at: datetime
    read: bool


class CustomerFeedResponse(ResponseModel):
    items: list[CustomerFeedItemResponse]
    unread_count: int
