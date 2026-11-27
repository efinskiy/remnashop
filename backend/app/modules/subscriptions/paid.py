from sqlalchemy import ColumnElement, Numeric, and_, exists, or_

from app.core.db.models.subscription import Subscription
from app.core.db.models.transaction import Transaction
from app.core.enums import TransactionStatus


def is_paid_subscription() -> ColumnElement[bool]:
    """A subscription money was paid for: sold at a price, or paid for since. A free
    plan, a promocode or bonus grant and a panel import carry 0 in the snapshot, and an
    imported one renewed for money keeps that 0, since a renewal leaves it."""
    return and_(
        Subscription.is_trial.is_(False),
        or_(
            Subscription.plan_snapshot["price_paid"].astext.cast(Numeric) > 0,
            exists().where(
                Transaction.fulfilled_subscription_id == Subscription.id,
                Transaction.status == TransactionStatus.PAID,
                Transaction.final_price > 0,
                Transaction.is_test.is_(False),
            ),
        ),
    )
