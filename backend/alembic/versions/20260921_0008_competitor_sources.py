"""Create competitor sources and link evidence to sources.

Revision ID: 20260921_0008
Revises: 20260921_0007
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0008"
down_revision: Union[str, Sequence[str], None] = "20260921_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "competitor_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competitor_research_id", sa.Integer(), nullable=False),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=True),
        sa.Column("discovery_method", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="discovered", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_category", sa.String(length=100), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["competitor_research_id"], ["competitor_research.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("competitor_research_id", "canonical_url"),
    )
    op.create_index(
        "ix_competitor_sources_competitor_research_id",
        "competitor_sources",
        ["competitor_research_id"],
    )
    op.add_column(
        "competitor_evidence",
        sa.Column("source_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_competitor_evidence_source_id",
        "competitor_evidence",
        "competitor_sources",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_competitor_evidence_source_id", "competitor_evidence", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_competitor_evidence_source_id", table_name="competitor_evidence")
    op.drop_constraint("fk_competitor_evidence_source_id", "competitor_evidence", type_="foreignkey")
    op.drop_column("competitor_evidence", "source_id")
    op.drop_index("ix_competitor_sources_competitor_research_id", table_name="competitor_sources")
    op.drop_table("competitor_sources")