from datetime import datetime
from typing import Literal, Optional

from app.core.dto import ResponseModel
from app.core.security.permissions import Permission


class GitInfoResponse(ResponseModel):
    commit_sha: Optional[str]
    commit_date: Optional[datetime]
    branch: Optional[str]
    is_official_build: bool


class SystemMetadataResponse(ResponseModel):
    version: str
    repository_url: str
    git: GitInfoResponse


class PermissionCatalogEntryResponse(ResponseModel):
    permission: Permission
    resource: str
    kind: Literal["read", "write"]
    token_grantable: bool
    admin_default: bool


class PermissionCatalogResponse(ResponseModel):
    items: list[PermissionCatalogEntryResponse]
    total: int
