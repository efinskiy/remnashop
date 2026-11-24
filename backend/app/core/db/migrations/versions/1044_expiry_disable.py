from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1044"
down_revision: Union[str, None] = "1043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "grace_settings",
        sa.Column("expiry_disable_enabled", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "grace_settings",
        sa.Column("expiry_disable_after_days", sa.Integer(), server_default="7", nullable=False),
    )
    op.add_column(
        "grace_settings",
        sa.Column("expiry_disable_warn_days", sa.Integer(), server_default="2", nullable=False),
    )
    op.add_column(
        "subscriptions",
        sa.Column("expiry_disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("expiry_disable_warned_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "expiry_disable_warned_at")
    op.drop_column("subscriptions", "expiry_disabled_at")
    op.drop_column("grace_settings", "expiry_disable_warn_days")
    op.drop_column("grace_settings", "expiry_disable_after_days")
    op.drop_column("grace_settings", "expiry_disable_enabled")
