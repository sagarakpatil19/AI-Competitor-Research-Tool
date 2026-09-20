"""Create competitor evidence table.

Revision ID: 20260921_0007
Revises: 20260921_0006
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0007"
down_revision: Union[str, Sequence[str], None] = "20260921_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "competitor_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competitor_research_id", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=True),
        sa.Column("source_type", sa.String(length=100), nullable=True),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["competitor_research_id"],
            ["competitor_research.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_competitor_evidence_competitor_research_id",
        "competitor_evidence",
        ["competitor_research_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_competitor_evidence_competitor_research_id",
        table_name="competitor_evidence",
    )
    op.drop_table("competitor_evidence")