from dataclasses import dataclass, field
from decimal import Decimal
from enum import auto
from typing import Final, Optional

from app.core.dto import BaseDto, TimestampMixin
from app.core.enums import Currency, RoundingMode, UpperStrEnum
from app.core.error_codes import ErrorCode
from app.core.exceptions import ValidationError


class PriceAdjustScope(UpperStrEnum):
    ALL_PLANS = auto()
    ALL_ADDONS = auto()
    SELECTED = auto()


class PriceAdjustMode(UpperStrEnum):
    MULTIPLY = auto()
    SET = auto()
    # plan durations only: the base duration's price per day times the days, less a
    # per-duration discount
    LADDER = auto()


class PinnedPriceAction(UpperStrEnum):
    KEEP = auto()
    # by the same ratio as the base price
    SCALE = auto()
    RESET = auto()


RATE_PRECISION: Final[Decimal] = Decimal("0.0000000001")
BASE_PRICE_PRECISION: Final[Decimal] = Decimal("0.01")
MIN_BASE_PRICE: Final[Decimal] = Decimal("0.01")
NON_ANCHOR_CURRENCIES: Final[frozenset[Currency]] = frozenset({Currency.XTR})


class CurrencyRateDto(BaseDto):
    currency: Currency
    rate: Decimal
    rounding_mode: RoundingMode
    charm_ending: Optional[int]
    min_amount: Decimal


@dataclass(frozen=True)
class CurrencyRateTable:
    anchor: Currency
    rows: dict[Currency, CurrencyRateDto] = field(default_factory=dict)

    def for_currency(self, c: Currency) -> CurrencyRateDto:
        row = self.rows.get(c)
        if row is None:
            raise ValidationError(
                f"No currency rate row for {c}", code=ErrorCode.CURRENCY_RATE_MISSING
            )
        return row

    def convert(self, amount: Decimal, source: Currency, target: Currency) -> Decimal:
        # exact, through the anchor; callers that show the result round it themselves
        if source is target:
            return amount
        return amount / self.for_currency(source).rate * self.for_currency(target).rate


class PricingSettingsDto(BaseDto, TimestampMixin):
    anchor_currency: Currency


@dataclass(frozen=True, kw_only=True)
class UpdateCurrencyRateDto:
    currency: Currency
    rate: Decimal
    rounding_mode: RoundingMode
    charm_ending: Optional[int]
    min_amount: Decimal
