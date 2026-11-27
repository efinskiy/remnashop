from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1045"
down_revision: Union[str, None] = "1044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "event_outbox", sa.Column("last_failed_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("event_outbox", "last_failed_at")
