from dataclasses import dataclass
from typing import ClassVar

from app.core.enums import Currency
from app.core.events import ActorEvent, EventCategory
from app.modules.pricing.dto import PinnedPriceAction, PriceAdjustMode, PriceAdjustScope


@dataclass(frozen=True, kw_only=True)
class CurrencyRateChangedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.PRICING
    currency: Currency
    old_rate: str
    new_rate: str


@dataclass(frozen=True, kw_only=True)
class AnchorSwitchedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.PRICING
    old_anchor: Currency
    new_anchor: Currency


@dataclass(frozen=True, kw_only=True)
class BasePricesAdjustedEvent(ActorEvent):
    category: ClassVar[EventCategory] = EventCategory.PRICING
    scope: PriceAdjustScope
    mode: PriceAdjustMode
    # the factor for MULTIPLY, the price for SET and LADDER
    value: str
    pinned: PinnedPriceAction
