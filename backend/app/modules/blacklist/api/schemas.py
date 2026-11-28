from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.dto import ResponseModel


class BlacklistResponse(ResponseModel):
    telegram_ids: list[int]
    emails: list[str]


class BlacklistSourceResponse(ResponseModel):
    id: int
    url: str
    name: Optional[str]
    enabled: bool
    entries_count: int
    last_synced_at: Optional[datetime]
    last_error: Optional[str]


class AddSourceRequest(BaseModel):
    url: str
    name: Optional[str] = None


class UpdateSourceRequest(BaseModel):
    enabled: bool


class BlacklistSourceListResponse(ResponseModel):
    items: list[BlacklistSourceResponse]
    total: int
