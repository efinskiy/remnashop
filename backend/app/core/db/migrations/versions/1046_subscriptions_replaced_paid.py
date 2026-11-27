from typing import Final, Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1046"
down_revision: Union[str, None] = "1045"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# every plan change so far, from the change events kept in the log (and any not yet
# moved there); a row replaced by one that was itself replaced passes the flag on
_BACKFILL: Final[str] = """
WITH RECURSIVE changes AS (
    SELECT (payload->>'previous_subscription_id')::int AS old_id,
           (payload->>'subscription_id')::int AS new_id
    FROM event_log_entries
    WHERE event_type IN ('SubscriptionChangedEvent', 'SubscriptionPlanChangedByAdminEvent')
    UNION
    SELECT (payload->>'previous_subscription_id')::int,
           (payload->>'subscription_id')::int
    FROM event_outbox
    WHERE event_type IN ('SubscriptionChangedEvent', 'SubscriptionPlanChangedByAdminEvent')
),
flagged AS (
    SELECT c.new_id
    FROM changes c
    JOIN subscriptions s ON s.id = c.old_id
    WHERE NOT s.is_trial
      AND (
          COALESCE((s.plan_snapshot->>'price_paid')::numeric, 0) > 0
          OR EXISTS (
              SELECT 1 FROM credit_segments cs WHERE cs.subscription_id = s.id AND cs.paid > 0
          )
      )
    UNION
    -- as at runtime: a trial in between isn't paid, so it passes nothing on
    SELECT c.new_id
    FROM changes c
    JOIN flagged f ON c.old_id = f.new_id
    JOIN subscriptions s ON s.id = f.new_id
    WHERE NOT s.is_trial
)
UPDATE subscriptions SET replaced_paid = true WHERE id IN (SELECT new_id FROM flagged)
"""


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("replaced_paid", sa.Boolean(), server_default="false", nullable=False),
    )
    op.execute(_BACKFILL)


def downgrade() -> None:
    op.drop_column("subscriptions", "replaced_paid")
