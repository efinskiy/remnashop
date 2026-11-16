from unittest.mock import AsyncMock, MagicMock

import app.modules.recurring_payments.usecases.get_own_recurring_payment as own_module
from app.modules.recurring_payments.usecases.get_own_recurring_payment import (
    GetOwnRecurringPaymentUseCase,
)
from tests.fakes.recurring import ShippedRecurringTermsTexts


async def test_state_skips_the_lookup_in_a_shop_without_auto_renewal(uow, monkeypatch) -> None:
    monkeypatch.setattr(own_module, "get_owned_target", AsyncMock())
    recurring = MagicMock(get=AsyncMock(return_value=None), consent_terms=AsyncMock())
    transactions = MagicMock(get_by_id=AsyncMock())
    gateways = MagicMock(
        get_by_type=AsyncMock(return_value=MagicMock(flags={"recurring_enabled": False})),
        get_raw_settings=AsyncMock(),
    )
    use_case = GetOwnRecurringPaymentUseCase(
        recurring, transactions, MagicMock(), gateways, uow, ShippedRecurringTermsTexts()
    )
    state = await use_case.system(7)
    assert not state.enabled and not state.available and not state.can_disable
    gateways.get_raw_settings.assert_not_awaited()
    recurring.consent_terms.assert_not_awaited()
