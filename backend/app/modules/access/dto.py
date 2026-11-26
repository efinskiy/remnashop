from dataclasses import dataclass
from enum import auto
from typing import Optional

from app.core.enums import AdLinkChannel, UpperStrEnum


class AccessDenial(UpperStrEnum):
    RESTRICTED = auto()
    REGISTRATION_DISABLED = auto()
    INVITE_ONLY = auto()


@dataclass(frozen=True, kw_only=True)
class CheckRegistrationAccessDto:
    channel: AdLinkChannel
    telegram_id: Optional[int] = None
    email: Optional[str] = None
    referral_code: Optional[str] = None
    ad_link_code: Optional[str] = None
