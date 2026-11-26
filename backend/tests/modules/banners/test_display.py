from app.core.constants import DEFAULT_BANNER_NAME
from app.core.enums import Locale
from app.modules.banners.display import find_banner_for_display
from app.modules.banners.dto import UploadBannerDto
from app.modules.banners.repository import BannerRepository


async def test_exact_match(banner_repository: BannerRepository) -> None:
    await banner_repository.upsert(
        UploadBannerDto(
            name="menu",
            locale=Locale.RU,
            content_type="image/jpeg",
            extension="jpg",
            size_bytes=1,
        )
    )

    banner = await find_banner_for_display(banner_repository, "menu", Locale.RU, Locale.EN)
    assert banner is not None
    assert banner.locale == Locale.RU


async def test_falls_back_to_default_name_same_locale(
    banner_repository: BannerRepository,
) -> None:
    await banner_repository.upsert(
        UploadBannerDto(
            name=DEFAULT_BANNER_NAME,
            locale=Locale.RU,
            content_type="image/jpeg",
            extension="jpg",
            size_bytes=1,
        )
    )

    banner = await find_banner_for_display(banner_repository, "menu", Locale.RU, Locale.EN)
    assert banner is not None
    assert banner.name == DEFAULT_BANNER_NAME
    assert banner.locale == Locale.RU


async def test_falls_back_to_requested_name_default_locale(
    banner_repository: BannerRepository,
) -> None:
    await banner_repository.upsert(
        UploadBannerDto(
            name="menu",
            locale=Locale.EN,
            content_type="image/jpeg",
            extension="jpg",
            size_bytes=1,
        )
    )

    banner = await find_banner_for_display(banner_repository, "menu", Locale.RU, Locale.EN)
    assert banner is not None
    assert banner.name == "menu"
    assert banner.locale == Locale.EN


async def test_falls_back_to_default_name_default_locale(
    banner_repository: BannerRepository,
) -> None:
    await banner_repository.upsert(
        UploadBannerDto(
            name=DEFAULT_BANNER_NAME,
            locale=Locale.EN,
            content_type="image/jpeg",
            extension="jpg",
            size_bytes=1,
        )
    )

    banner = await find_banner_for_display(banner_repository, "menu", Locale.RU, Locale.EN)
    assert banner is not None
    assert banner.name == DEFAULT_BANNER_NAME
    assert banner.locale == Locale.EN


async def test_returns_none_when_nothing_matches(
    banner_repository: BannerRepository,
) -> None:
    banner = await find_banner_for_display(banner_repository, "menu", Locale.RU, Locale.EN)
    assert banner is None
