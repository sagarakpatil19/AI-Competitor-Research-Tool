"""Add evidence processing and validation metadata.

Revision ID: 20260921_0009
Revises: 20260921_0008
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0009"
down_revision: Union[str, Sequence[str], None] = "20260921_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "competitor_evidence",
        sa.Column("processing_status", sa.String(length=32), server_default="pending", nullable=False),
    )
    op.add_column(
        "competitor_evidence",
        sa.Column("validation_status", sa.String(length=32), server_default="pending", nullable=False),
    )
    op.add_column("competitor_evidence", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column("competitor_evidence", sa.Column("validation_reason", sa.Text(), nullable=True))
    op.add_column("competitor_evidence", sa.Column("normalized_content", sa.Text(), nullable=True))
    op.add_column("competitor_evidence", sa.Column("normalized_excerpt", sa.Text(), nullable=True))
    op.add_column(
        "competitor_evidence",
        sa.Column("normalized_content_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "competitor_evidence",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_competitor_evidence_research_processing_validation",
        "competitor_evidence",
        ["competitor_research_id", "processing_status", "validation_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_competitor_evidence_research_processing_validation",
        table_name="competitor_evidence",
    )
    op.drop_column("competitor_evidence", "processed_at")
    op.drop_column("competitor_evidence", "normalized_content_hash")
    op.drop_column("competitor_evidence", "normalized_excerpt")
    op.drop_column("competitor_evidence", "normalized_content")
    op.drop_column("competitor_evidence", "validation_reason")
    op.drop_column("competitor_evidence", "processing_error")
    op.drop_column("competitor_evidence", "validation_status")
    op.drop_column("competitor_evidence", "processing_status")