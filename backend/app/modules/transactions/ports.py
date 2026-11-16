from typing import Protocol, Union

from app.core.enums import Locale
from app.modules.transactions.dto import PaymentTextDto, RecurringTermsTextDto, TransactionDto


class PromocodeLiveness(Protocol):
    async def is_live(self, promocode_id: int) -> bool: ...


class PaymentsRestoredNotifier(Protocol):
    # queues the "payments are back" notice for each user, as a notification of that outbox event
    async def notify(self, user_ids: list[int], outbox_id: int) -> None: ...


class PaymentTexts(Protocol):
    # what the provider shows the customer for the order
    async def describe(self, order: TransactionDto, locale: Locale) -> PaymentTextDto: ...


class RecurringTermsTexts(Protocol):
    async def render(
        self, locale: Locale, args: dict[str, Union[str, int]]
    ) -> RecurringTermsTextDto: ...
