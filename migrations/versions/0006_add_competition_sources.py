"""Add sources column to competition_assessments (R1 web-grounded research).

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "competition_assessments",
        sa.Column("sources", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("competition_assessments", "sources")
