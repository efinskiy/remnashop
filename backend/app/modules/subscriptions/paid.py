from sqlalchemy import ColumnElement, Numeric, and_, exists, or_

from app.core.db.models.credit_segment import CreditSegment
from app.core.db.models.subscription import Subscription


def is_paid_subscription() -> ColumnElement[bool]:
    """Not a trial, and money was paid for it: sold at a price, or a stretch of its term
    paid for. The snapshot holds only the price of the sale or plan change that made the
    row; the segments hold a renewal's price and the credit a plan change carries over.
    Segments written by migration 1027 can say 0 for a term sold for money, renewed free
    after it lapsed; the snapshot keeps that sale."""
    return and_(
        Subscription.is_trial.is_(False),
        or_(
            Subscription.plan_snapshot["price_paid"].astext.cast(Numeric) > 0,
            exists().where(
                CreditSegment.subscription_id == Subscription.id, CreditSegment.paid > 0
            ),
        ),
    )
