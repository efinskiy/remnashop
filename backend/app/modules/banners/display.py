from typing import Optional

from app.core.constants import DEFAULT_BANNER_NAME
from app.core.enums import Locale
from app.modules.banners.dto import BannerDto
from app.modules.banners.repository import BannerRepository


async def find_banner_for_display(
    repo: BannerRepository, name: str, locale: Locale, default_locale: Locale
) -> Optional[BannerDto]:
    """The banner a window shows: its own before the default banner, the reader's
    language before the default one."""
    candidates = [(name, locale), (DEFAULT_BANNER_NAME, locale)]
    if locale != default_locale:
        candidates += [(name, default_locale), (DEFAULT_BANNER_NAME, default_locale)]
    for candidate_name, candidate_locale in candidates:
        banner = await repo.get(candidate_name, candidate_locale)
        if banner is not None:
            return banner
    return None
