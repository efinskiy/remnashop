from dataclasses import dataclass
from typing import Literal, Optional

import httpx
from loguru import logger

from app.modules.recurring_payments.policy import RecurringReason
from app.modules.transactions import PaymentTextDto, TransactionDto, YooKassaGateway


@dataclass(frozen=True)
class RecurringSubmission:
    outcome: Literal["accepted", "merchant", "configuration", "ambiguous"]
    payment_id: Optional[str] = None
    reason: Optional[RecurringReason] = None


async def submit_recurring(
    gateway: YooKassaGateway,
    order: TransactionDto,
    text: PaymentTextDto,
    payment_method: str,
    *,
    first_attempt: bool,
) -> RecurringSubmission:
    try:
        intent = await gateway.create_recurring_payment(order, text, payment_method)
    except httpx.HTTPStatusError as error:
        code = error.response.status_code
        logger.warning(f"YooKassa order '{order.id}' rejected with HTTP {code}")
        if code not in {400, 401, 403, 404}:
            raise
        if not first_attempt:
            return RecurringSubmission("ambiguous", reason=RecurringReason.MERCHANT_UNAVAILABLE)
        if code in {401, 403}:
            return RecurringSubmission("merchant", reason=RecurringReason.MERCHANT_UNAVAILABLE)
        # the error body's wording isn't a contract, so it never decides whose problem this is
        return RecurringSubmission(
            "configuration", reason=RecurringReason.PROVIDER_REQUEST_REJECTED
        )
    return RecurringSubmission("accepted", intent.provider_payment_id)
