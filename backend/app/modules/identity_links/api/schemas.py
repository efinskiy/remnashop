from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.core.constants import EMAIL_PATTERN
from app.core.dto import ResponseModel
from app.core.enums import Locale
from app.modules.identity_links.dto import IdentityKind


class LinkEmailCodeRequest(BaseModel):
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    locale: Locale = Locale.EN


class LinkEmailVerifyRequest(BaseModel):
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    code: str = Field(pattern=r"^\d{6}$")


class IdentityResponse(ResponseModel):
    kind: IdentityKind
    linked: bool
    label: Optional[str]
    editable: bool


class IdentitiesResponse(ResponseModel):
    items: list[IdentityResponse]
    total: int


class MergeRequest(BaseModel):
    merge_token: str = Field(min_length=1, max_length=128)


class IdentityMergePreviewResponse(ResponseModel):
    subscriptions: int
    transactions: int
    referrals: int
    identities: list[IdentityResponse]


# the answer of every link flow (email, bot, OAuth)
class LinkResultResponse(ResponseModel):
    status: Literal["linked", "already_linked", "merge_required"]
    merge_token: Optional[str] = None
    expires_in: Optional[int] = None
    other: Optional[IdentityMergePreviewResponse] = None


class LinkTelegramSignInRequest(BaseModel):
    token: str = Field(max_length=128)


class LinkDeeplinkResponse(ResponseModel):
    bot_url: str
    expires_in: int


class LinkOAuthAuthorizeResponse(ResponseModel):
    url: str


class LinkOAuthCallbackRequest(BaseModel):
    code: str = Field(max_length=2048)
    state: str = Field(max_length=256)
