from datetime import datetime
from typing import Final, Optional

from pydantic import BaseModel, ConfigDict

SERVER_OWNED_FIELDS: Final[frozenset[str]] = frozenset({"id", "created_at", "updated_at"})


class BaseDto(BaseModel):
    model_config = ConfigDict(strict=False, extra="ignore")

    # 0 = not persisted yet (excluded via SERVER_OWNED_FIELDS); serial PKs never
    # assign 0, so no Optional. Don't truth-test `id`.
    id: int = 0


class TimestampMixin(BaseModel):
    model_config = ConfigDict(strict=False, extra="ignore")

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResponseModel(BaseModel):
    # every response sends every field, so a default doesn't make one optional
    # in the schema the dashboard's types are generated from
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)
