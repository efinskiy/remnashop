import importlib
from types import ModuleType
from typing import Final

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_MIGRATION: Final[ModuleType] = importlib.import_module(
    "app.core.db.migrations.versions.1047_shop_timezone"
)


async def _with_report_timezone(session: AsyncSession, zone: str) -> None:
    # the column 1047 drops, back for this test's transaction only
    await session.execute(
        text("ALTER TABLE notification_settings ADD COLUMN report_timezone varchar(64)")
    )
    await session.execute(text("DELETE FROM notification_settings"))
    await session.execute(
        text("INSERT INTO notification_settings (id, report_timezone) VALUES (1, :zone)"),
        {"zone": zone},
    )
    await session.execute(text("DELETE FROM shop_settings"))


async def test_the_report_zone_becomes_the_shops_with_the_default_cap(
    session: AsyncSession,
) -> None:
    await _with_report_timezone(session, "Europe/Moscow")

    await session.execute(text(_MIGRATION._COPY_ZONE))

    row = (
        await session.execute(text("SELECT max_active_subscriptions, timezone FROM shop_settings"))
    ).one()
    # NULL would mean unlimited subscriptions
    assert tuple(row) == (3, "Europe/Moscow")


async def test_a_utc_report_zone_leaves_the_shop_row_alone(session: AsyncSession) -> None:
    await _with_report_timezone(session, "UTC")

    await session.execute(text(_MIGRATION._COPY_ZONE))

    assert (await session.execute(text("SELECT count(*) FROM shop_settings"))).scalar() == 0
