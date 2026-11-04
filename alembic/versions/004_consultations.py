"""Create consultations table for analytics / etapa 6 persistence slice

Revision ID: 004_consultations
Revises: 003_epok_rubro_id
Create Date: 2026-10-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_consultations"
down_revision: Union[str, None] = "003_epok_rubro_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consultations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("data_status_overall", sa.String(length=32), nullable=True),
        sa.Column("activity_code", sa.String(length=64), nullable=True),
        sa.Column("activity_name", sa.String(length=255), nullable=True),
        sa.Column("original_query", sa.Text(), nullable=True),
        sa.Column("commune", sa.String(length=64), nullable=True),
        sa.Column("neighborhood", sa.String(length=128), nullable=True),
        sa.Column("normalized_address", sa.String(length=512), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("zoning_mixtura", sa.String(length=64), nullable=True),
        sa.Column("zoning_rubro_allowed", sa.Boolean(), nullable=True),
        sa.Column("zoning_status", sa.String(length=64), nullable=True),
        sa.Column("source_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consultations_created_at", "consultations", ["created_at"])
    op.create_index("ix_consultations_status", "consultations", ["status"])
    op.create_index("ix_consultations_activity_code", "consultations", ["activity_code"])
    op.create_index("ix_consultations_commune", "consultations", ["commune"])
    op.create_index("ix_consultations_neighborhood", "consultations", ["neighborhood"])


def downgrade() -> None:
    op.drop_index("ix_consultations_neighborhood", table_name="consultations")
    op.drop_index("ix_consultations_commune", table_name="consultations")
    op.drop_index("ix_consultations_activity_code", table_name="consultations")
    op.drop_index("ix_consultations_status", table_name="consultations")
    op.drop_index("ix_consultations_created_at", table_name="consultations")
    op.drop_table("consultations")
