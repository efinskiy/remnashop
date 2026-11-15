from app.core.actor import Actor
from app.core.db.uow import UnitOfWork
from app.core.exceptions import PaymentGatewayError
from app.core.usecase import UseCase
from app.modules.transactions.dto import CheckRecurringPaymentDto
from app.modules.transactions.recurring_poller import RecurringPoller
from app.modules.transactions.recurring_repository import RecurringPaymentRepository
from app.modules.transactions.repository import TransactionRepository


class CheckRecurringPaymentUseCase(UseCase[CheckRecurringPaymentDto, None]):
    required_permission = None

    def __init__(
        self,
        recurring_repository: RecurringPaymentRepository,
        transaction_repository: TransactionRepository,
        recurring_poller: RecurringPoller,
        uow: UnitOfWork,
    ) -> None:
        self._recurring = recurring_repository
        self._transactions = transaction_repository
        self._poller = recurring_poller
        self._uow = uow

    async def _execute(self, actor: Actor, data: CheckRecurringPaymentDto) -> None:
        async with self._uow:
            mandate = await self._recurring.get(data.subscription_id)
            if mandate is None or mandate.pending_transaction_id != data.transaction_id:
                raise PaymentGatewayError("The pending payment changed; refresh its status")
            order = await self._transactions.get_by_id(data.transaction_id)
            gateway = await self._poller.gateway()
            if order.external_payment_id is None or mandate.shop_id != gateway.settings.shop_id:
                raise PaymentGatewayError("No payment can be checked with the current shop")
        await self._poller.poll(data.subscription_id, order, gateway)
