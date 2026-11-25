from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.core.dto import ResponseModel


class EmojiPackItemResponse(ResponseModel):
    custom_emoji_id: str
    fallback_emoji: str
    # null when this emoji has no animation stored
    animation_kind: Optional[Literal["lottie", "video"]]


class EmojiPackResponse(ResponseModel):
    set_name: str
    title: str
    items: list[EmojiPackItemResponse]


class ImportEmojiPackRequest(BaseModel):
    link: str = Field(min_length=1, max_length=256)


class EmojiPackListResponse(ResponseModel):
    items: list[EmojiPackResponse]
    total: int
