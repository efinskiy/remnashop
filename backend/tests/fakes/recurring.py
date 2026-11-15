from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.uow import UnitOfWork
from app.core.outbox_event_publisher import OutboxEventPublisher
from app.modules.transactions.recurring_lifecycle import RecurringLifecycle
from app.modules.transactions.recurring_repository import RecurringPaymentRepository
from app.modules.transactions.repository import TransactionRepository
from tests.fakes.dispatch import RecordingDispatch


def make_recurring_lifecycle(session: AsyncSession) -> RecurringLifecycle:
    return RecurringLifecycle(
        RecurringPaymentRepository(session),
        TransactionRepository(session),
        OutboxEventPublisher(UnitOfWork(session), RecordingDispatch()),
    )


async def fulfil(session: AsyncSession, order_id: int, subscription_id: int) -> None:
    """mark_fulfilled plus the mandate update its usecases run after it"""
    marked = await TransactionRepository(session).mark_fulfilled(order_id, subscription_id)
    if marked is not None:
        await make_recurring_lifecycle(session).on_fulfilled(marked, subscription_id)
