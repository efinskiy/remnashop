from datetime import timedelta

from app.core.db.models import RecurringPayment
from app.core.utils.time import datetime_now
from app.modules.transactions.recurring_repository import RecurringPaymentRepository
from app.modules.transactions.usecases.wipe_stale_payment_methods import (
    WipeStalePaymentMethodsUseCase,
)
from tests.modules.transactions import test_recurring_payments as cases

case = cases.case


async def _withdrawn(case, session, uow, *, days: int, pending: bool = False) -> None:  # type: ignore[no-untyped-def]
    async with uow:
        row = await session.get(RecurringPayment, case.subscription.id)
        row.customer_disabled = True
        row.enabled = False
        row.disabled_at = datetime_now() - timedelta(days=days)
        if pending:
            row.pending_transaction_id = case.source.id
        await session.flush()


async def test_wipe_after_30_days_only(case, session, uow) -> None:
    repository = RecurringPaymentRepository(session)
    use_case = WipeStalePaymentMethodsUseCase(repository, uow)
    await _withdrawn(case, session, uow, days=29)
    await use_case.system()
    assert (await repository.get(case.subscription.id)).payment_method_id is not None
    await _withdrawn(case, session, uow, days=31, pending=True)
    await use_case.system()
    assert (await repository.get(case.subscription.id)).payment_method_id is not None
    await _withdrawn(case, session, uow, days=31)
    async with uow:
        row = await session.get(RecurringPayment, case.subscription.id)
        row.pending_transaction_id = None
    await use_case.system()
    assert (await repository.get(case.subscription.id)).payment_method_id is None
