from dataclasses import dataclass
from enum import auto
from typing import Optional

from app.core.enums import UpperStrEnum


class EmailOutcome(UpperStrEnum):
    SENT = auto()
    REFUSED = auto()
    RETRY = auto()


@dataclass(frozen=True, kw_only=True)
class EmailMessageDto:
    to: str
    subject: str
    text: str
    html: str


@dataclass(frozen=True, kw_only=True)
class SendTestEmailDto:
    bulk: bool


@dataclass(frozen=True, kw_only=True)
class EmailBrandDto:
    brand: str
    color: Optional[str]
    has_logo: bool
