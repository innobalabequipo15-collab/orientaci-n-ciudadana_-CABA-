"""consultation_follow_ups table

Revision ID: 005_consultation_follow_ups
Revises: 004_consultations
Create Date: 2026-10-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_consultation_follow_ups"
down_revision: Union[str, None] = "004_consultations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consultation_follow_ups",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("consultation_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="mock"),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_consultation_follow_ups_consultation_id",
        "consultation_follow_ups",
        ["consultation_id"],
    )
    op.create_index(
        "ix_consultation_follow_ups_created_at",
        "consultation_follow_ups",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_consultation_follow_ups_created_at", table_name="consultation_follow_ups")
    op.drop_index(
        "ix_consultation_follow_ups_consultation_id",
        table_name="consultation_follow_ups",
    )
    op.drop_table("consultation_follow_ups")
