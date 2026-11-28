from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.dto import ResponseModel


class SlideResponse(ResponseModel):
    image_url: Optional[str]
    text: dict[str, str]
    url: Optional[str]
    url_label: dict[str, str]


class AnnouncementResponse(ResponseModel):
    id: str
    icon: str
    severity: str
    title: dict[str, str]
    text: dict[str, str]
    url: Optional[str]
    url_label: dict[str, str]
    notify_at: datetime
    auto_open: bool
    slides: list[SlideResponse]
    seen: bool


class AnnouncementListResponse(ResponseModel):
    items: list[AnnouncementResponse]
    total: int


class AnnouncementIdsRequest(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=100)
