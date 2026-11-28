from contextvars import copy_context
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.utils.time import datetime_now
from app.telegram.i18n import format_date, format_datetime, use_shop_zone


def test_format_expire_time_future() -> None:
    expiry = datetime_now() + timedelta(days=5, hours=3)
    result = format_datetime(expiry)
    assert result == expiry.strftime("%d.%m.%Y %H:%M")


def test_format_expire_time_none() -> None:
    assert format_datetime(None) == "—"


def test_dates_are_written_as_the_shops_day() -> None:
    # 22:30 UTC on the 7th is already 01:30 on the 8th in Moscow
    late = datetime(2026, 10, 7, 22, 30, tzinfo=UTC)

    def in_moscow() -> tuple[str, str]:
        use_shop_zone(ZoneInfo("Europe/Moscow"))
        return format_date(late), format_datetime(late)

    # a copied context: the zone set for this "update" doesn't leak into other tests
    assert copy_context().run(in_moscow) == ("08.10.2026", "08.10.2026 01:30")
    assert format_date(late) == "07.10.2026"
