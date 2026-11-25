from typing import Optional

from pydantic import BaseModel

from app.core.dto import ResponseModel


class OAuthConnectAuthorizeResponse(ResponseModel):
    url: str


class OAuthConnectCallbackRequest(BaseModel):
    code: str
    state: str


class OAuthIdentityResponse(ResponseModel):
    provider: str
    external_login: Optional[str] = None


class OAuthIdentityListResponse(ResponseModel):
    items: list[OAuthIdentityResponse]
    total: int
