from typing import Literal, Optional

from pydantic import BaseModel

from app.core.dto import ResponseModel
from app.modules.users import UserResponse


class MergeConflictResponse(ResponseModel):
    key: str
    source_value: Optional[str]
    target_value: Optional[str]
    forced: Optional[Literal["source", "target"]]


class MergeReferrerCycleResponse(ResponseModel):
    side: Literal["source", "target"]
    referrer_id: int


class MergeCountsResponse(ResponseModel):
    subscriptions: int
    transactions: int
    referrals: int
    passkeys: int
    oauth_identities: int


class MergePreviewResponse(ResponseModel):
    source: UserResponse
    target: UserResponse
    conflicts: list[MergeConflictResponse]
    referrer_cycles: list[MergeReferrerCycleResponse]
    source_counts: MergeCountsResponse
    fingerprint: str


class MergeAccountsRequest(BaseModel):
    source_id: int
    fingerprint: str
    choices: dict[str, Literal["source", "target"]] = {}
