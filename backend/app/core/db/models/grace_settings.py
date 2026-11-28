from typing import Optional
from uuid import UUID

from remnapy.enums import TrafficLimitStrategy
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import (
    EXPIRY_DISABLE_DEFAULT_AFTER_DAYS,
    EXPIRY_DISABLE_DEFAULT_WARN_DAYS,
    GRACE_DEFAULT_DURATION_DAYS,
)
from app.core.db.base import BaseSql
from app.core.db.timestamp import TimestampMixin


class GraceSettings(BaseSql, TimestampMixin):
    __tablename__ = "grace_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    enabled: Mapped[bool] = mapped_column(default=False, server_default="false")
    internal_squads: Mapped[list[UUID]] = mapped_column(default=list, server_default="{}")
    external_squad: Mapped[Optional[UUID]]
    traffic_limit_mb: Mapped[int] = mapped_column(default=0, server_default="0")
    traffic_limit_strategy: Mapped[TrafficLimitStrategy] = mapped_column(
        default=TrafficLimitStrategy.NO_RESET, server_default=TrafficLimitStrategy.NO_RESET.name
    )
    tag: Mapped[Optional[str]]
    duration_days: Mapped[int] = mapped_column(
        default=GRACE_DEFAULT_DURATION_DAYS, server_default=str(GRACE_DEFAULT_DURATION_DAYS)
    )
    # the panel user of a subscription expired this many days (counted from grace's end)
    # is switched off; independent of grace itself
    expiry_disable_enabled: Mapped[bool] = mapped_column(default=False, server_default="false")
    expiry_disable_after_days: Mapped[int] = mapped_column(
        default=EXPIRY_DISABLE_DEFAULT_AFTER_DAYS,
        server_default=str(EXPIRY_DISABLE_DEFAULT_AFTER_DAYS),
    )
    # 0: no warning
    expiry_disable_warn_days: Mapped[int] = mapped_column(
        default=EXPIRY_DISABLE_DEFAULT_WARN_DAYS,
        server_default=str(EXPIRY_DISABLE_DEFAULT_WARN_DAYS),
    )
