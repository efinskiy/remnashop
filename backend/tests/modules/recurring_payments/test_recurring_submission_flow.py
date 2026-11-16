import json

import pytest

from app.core.enums import PaymentGatewayType, PurchaseChannel, TransactionStatus
from app.modules.recurring_payments.dto import SetRecurringPaymentDto
from app.modules.transactions.dto import HandleWebhookDto, WebhookRequest
from app.modules.transactions.usecases import HandlePaymentWebhookUseCase
from tests.fakes.events import RecordingEventPublisher
from tests.fakes.recurring import make_recurring_lifecycle
from tests.modules.recurring_payments import test_recurring_payments as cases

case = cases.case


@pytest.fixture(autouse=True)
def production_session_mode(session):
    session.autoflush = False


async def test_post_runs_without_open_transaction(case, session) -> None:
    observed: list[bool] = []

    async def hook(payment_id: str) -> None:
        observed.append(session.in_transaction())

    case.provider.on_post = hook
    await case.worker.system()
    assert observed == [False]


async def test_disable_during_post_stops_next_cycle(case, session, uow) -> None:
    states = []

    async def hook(payment_id: str) -> None:
        await case.set_state(
            case.user,
            SetRecurringPaymentDto(
                subscription_id=case.subscription.id, enabled=False, channel=PurchaseChannel.CABINET
            ),
        )
        states.append(await case.get_state(case.user, case.subscription.id))

    case.provider.on_post = hook
    await case.worker.system()
    case.provider.on_post = None
    assert states and states[0].payment_in_flight and not states[0].enabled
    await cases._tick_again(case, uow)
    assert len(case.provider.posts) == 1
    mandate = await case.repository.get(case.subscription.id)
    assert mandate.customer_disabled and not mandate.enabled


async def test_webhook_before_record_settles_once(
    case, session, uow, transaction_repository, gateway_repository, user_repository
) -> None:
    handler = HandlePaymentWebhookUseCase(
        transaction_repository,
        gateway_repository,
        case.worker._poller._factory,
        user_repository,
        RecordingEventPublisher(),
        uow,
        case.dispatch,
        make_recurring_lifecycle(session),
    )
    seen: list[int] = []

    async def hook(payment_id: str) -> None:
        mandate = await case.repository.get(case.subscription.id)
        order = await transaction_repository.get_by_id(mandate.pending_transaction_id)
        seen.append(order.id)
        await handler.system(
            HandleWebhookDto(
                gateway_type=PaymentGatewayType.YOOKASSA,
                request=WebhookRequest(
                    body=json.dumps(
                        {
                            "event": "payment.succeeded",
                            "object": {
                                "id": payment_id,
                                "metadata": {"order_ref": order.idempotency_key},
                            },
                        }
                    ).encode(),
                    headers={},
                    client_ip="185.71.76.1",
                ),
            )
        )

    case.provider.on_post = hook
    await case.worker.system()
    case.provider.on_post = None
    order = await transaction_repository.get_by_id(seen[0])
    assert order.status is TransactionStatus.PAID
    assert len(case.dispatch.messages) == 1
    await cases._tick_again(case, uow)
    assert len(case.provider.posts) == 1 and len(case.dispatch.messages) == 1
