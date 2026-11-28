from typing import Final, Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1047"
down_revision: Union[str, None] = "1046"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# the daily report's zone becomes the shop's; a missing shop row is created with the
# subscription cap a missing row reads as (3), since NULL there means unlimited
_COPY_ZONE: Final[str] = """
INSERT INTO shop_settings (id, max_active_subscriptions, timezone)
SELECT id, 3, report_timezone FROM notification_settings
WHERE id = 1 AND report_timezone <> 'UTC'
ON CONFLICT (id) DO UPDATE SET timezone = EXCLUDED.timezone
"""

_COPY_ZONE_BACK: Final[str] = """
UPDATE notification_settings SET report_timezone = shop_settings.timezone
FROM shop_settings WHERE notification_settings.id = 1 AND shop_settings.id = 1
"""


def upgrade() -> None:
    op.add_column(
        "shop_settings",
        sa.Column("timezone", sa.String(length=64), server_default="UTC", nullable=False),
    )
    op.execute(_COPY_ZONE)
    op.drop_column("notification_settings", "report_timezone")


def downgrade() -> None:
    op.add_column(
        "notification_settings",
        sa.Column("report_timezone", sa.String(length=64), server_default="UTC", nullable=False),
    )
    op.execute(_COPY_ZONE_BACK)
    op.drop_column("shop_settings", "timezone")
