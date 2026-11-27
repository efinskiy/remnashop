from sqlalchemy import ColumnElement, and_, exists

from app.core.db.models.credit_segment import CreditSegment
from app.core.db.models.subscription import Subscription


def is_paid_subscription() -> ColumnElement[bool]:
    """Not a trial, and money was paid for some stretch of its term. The segments hold
    it: a renewal's price, the credit a plan change carries over, a migrated term, and a
    renewal's refund takes its own back. The snapshot's price can't tell: a renewal leaves it, and
    a plan change paid by credit or made by an admin writes 0."""
    return and_(
        Subscription.is_trial.is_(False),
        exists().where(CreditSegment.subscription_id == Subscription.id, CreditSegment.paid > 0),
    )
