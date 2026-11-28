from decimal import Decimal
from typing import Optional

import pytest

from app.core.db.uow import UnitOfWork
from app.core.enums import AddOnType, Currency, PlanType
from app.core.error_codes import ErrorCode
from app.core.exceptions import ValidationError
from app.core.ports import EventPublisher
from app.modules.plans.addon_repository import AddOnRepository
from app.modules.plans.dto import (
    AddOnDto,
    CreateAddOnDto,
    CreatePlanDto,
    PlanDto,
    SetAddOnPriceOverrideDto,
    SetMatrixPricesDto,
    SetPlanDurationDto,
    SetPlanDurationsDto,
    SetPlanPriceOverrideDto,
)
from app.modules.plans.repository import PlanRepository
from app.modules.plans.usecases import SetMatrixPricesUseCase
from app.modules.pricing.repository import PricingRepository


async def _plan_with_duration(plan_repository: PlanRepository) -> PlanDto:
    plan = await plan_repository.create(
        CreatePlanDto(
            public_code="anchor", name="Anchor", type=PlanType.BOTH, traffic_limit=1, device_limit=1
        )
    )
    return await plan_repository.set_durations(
        SetPlanDurationsDto(
            plan_id=plan.id,
            durations=[SetPlanDurationDto(days=30, order_index=0, base_price=Decimal("3.99"))],
        )
    )


async def _addon(addon_repository: AddOnRepository) -> AddOnDto:
    return await addon_repository.create(
        CreateAddOnDto(name="anchor", type=AddOnType.TRAFFIC, amount=1, base_price=Decimal("1"))
    )


@pytest.fixture
async def anchor(pricing_repository: PricingRepository) -> Currency:
    return (await pricing_repository.get_settings()).anchor_currency


@pytest.fixture
def use_case(
    plan_repository: PlanRepository,
    addon_repository: AddOnRepository,
    pricing_repository: PricingRepository,
    uow: UnitOfWork,
    event_publisher: EventPublisher,
) -> SetMatrixPricesUseCase:
    return SetMatrixPricesUseCase(
        plan_repository, addon_repository, pricing_repository, uow, event_publisher
    )


def _plan_override(
    plan_id: int, currency: Currency, price: Optional[Decimal]
) -> SetMatrixPricesDto:
    return SetMatrixPricesDto(
        plan_base_prices=[],
        plan_overrides=[
            SetPlanPriceOverrideDto(plan_id=plan_id, days=30, currency=currency, price=price)
        ],
        addon_base_prices=[],
        addon_overrides=[],
    )


def _addon_override(
    addon_id: int, currency: Currency, price: Optional[Decimal]
) -> SetMatrixPricesDto:
    return SetMatrixPricesDto(
        plan_base_prices=[],
        plan_overrides=[],
        addon_base_prices=[],
        addon_overrides=[
            SetAddOnPriceOverrideDto(addon_id=addon_id, currency=currency, price=price)
        ],
    )


async def test_plan_override_in_the_anchor_currency_is_rejected(
    plan_repository: PlanRepository, use_case: SetMatrixPricesUseCase, anchor: Currency
) -> None:
    plan = await _plan_with_duration(plan_repository)

    with pytest.raises(ValidationError) as exc_info:
        await use_case.system(_plan_override(plan.id, anchor, Decimal("5")))

    assert exc_info.value.code is ErrorCode.ANCHOR_PRICE_NOT_OVERRIDABLE


async def test_plan_override_stranded_in_the_anchor_currency_can_be_cleared(
    plan_repository: PlanRepository, use_case: SetMatrixPricesUseCase, anchor: Currency
) -> None:
    # pinned while another currency was the anchor
    plan = await _plan_with_duration(plan_repository)
    await plan_repository.set_price_override(
        SetPlanPriceOverrideDto(plan_id=plan.id, days=30, currency=anchor, price=Decimal("5"))
    )

    await use_case.system(_plan_override(plan.id, anchor, None))

    assert (await plan_repository.get_by_id(plan.id)).durations[0].overrides == []


async def test_addon_override_in_the_anchor_currency_is_rejected(
    addon_repository: AddOnRepository, use_case: SetMatrixPricesUseCase, anchor: Currency
) -> None:
    addon = await _addon(addon_repository)

    with pytest.raises(ValidationError) as exc_info:
        await use_case.system(_addon_override(addon.id, anchor, Decimal("2")))

    assert exc_info.value.code is ErrorCode.ANCHOR_PRICE_NOT_OVERRIDABLE


async def test_addon_override_stranded_in_the_anchor_currency_can_be_cleared(
    addon_repository: AddOnRepository, use_case: SetMatrixPricesUseCase, anchor: Currency
) -> None:
    addon = await _addon(addon_repository)
    await addon_repository.set_price_override(
        SetAddOnPriceOverrideDto(addon_id=addon.id, currency=anchor, price=Decimal("2"))
    )

    await use_case.system(_addon_override(addon.id, anchor, None))

    assert (await addon_repository.get_by_id(addon.id)).overrides == []
