"""Create the competition_assessments table (competition research).

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "competition_assessments",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_name", sa.String(), nullable=False),
        sa.Column("saturation", sa.String(), nullable=False),
        sa.Column("market_gap", sa.Text(), nullable=True),
        sa.Column("competitors", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("competition_assessments")
