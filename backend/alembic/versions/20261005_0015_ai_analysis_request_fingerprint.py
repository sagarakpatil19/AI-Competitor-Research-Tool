"""Add persistent reusable AI analysis request identity.

Revision ID: 20261005_0015
Revises: 20261005_0014
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261005_0015"
down_revision: Union[str, Sequence[str], None] = "20261005_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_analyses",
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "uq_ai_analyses_reusable_request_fingerprint",
        "ai_analyses",
        ["request_fingerprint"],
        unique=True,
        postgresql_where=sa.text(
            "request_fingerprint IS NOT NULL AND status IN ('pending', 'running', 'completed')"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_ai_analyses_reusable_request_fingerprint",
        table_name="ai_analyses",
    )
    op.drop_column("ai_analyses", "request_fingerprint")
