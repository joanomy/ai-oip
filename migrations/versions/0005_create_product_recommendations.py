"""Create the product_recommendations table (product recommendation).

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_recommendations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_name", sa.String(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(), nullable=False),
        sa.Column("product_concept", sa.Text(), nullable=False),
        sa.Column("mvp_scope", sa.JSON(), nullable=False),
        sa.Column("differentiation", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
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
    op.drop_table("product_recommendations")
