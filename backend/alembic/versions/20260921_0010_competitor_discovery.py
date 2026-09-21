"""Create competitor discovery data foundation.

Revision ID: 20260921_0010
Revises: 20260921_0009
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0010"
down_revision: Union[str, Sequence[str], None] = "20260921_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "competitor_discovery_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_run_id", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("failure_category", sa.String(length=100), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'no_candidates')",
            name="ck_competitor_discovery_runs_status",
        ),
    )
    op.create_index(
        "ix_competitor_discovery_runs_research_created",
        "competitor_discovery_runs",
        ["research_run_id", "created_at"],
    )

    op.create_table(
        "competitor_discovery_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("discovery_run_id", sa.Integer(), nullable=False),
        sa.Column("research_run_id", sa.Integer(), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("discovery_method", sa.String(length=100), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("provider_candidate_id", sa.String(length=255), nullable=True),
        sa.Column("provider_rank", sa.Integer(), nullable=True),
        sa.Column("discovery_status", sa.String(length=32), server_default="received", nullable=False),
        sa.Column("validation_status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("validation_reason", sa.Text(), nullable=True),
        sa.Column("competitor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["discovery_run_id"], ["competitor_discovery_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competitor_id"], ["competitors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "discovery_status IN ('received', 'normalized', 'duplicate', 'failed')",
            name="ck_competitor_discovery_candidates_discovery_status",
        ),
        sa.CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid', 'same_company', 'rejected', 'promoted')",
            name="ck_competitor_discovery_candidates_validation_status",
        ),
    )
    op.create_index(
        "ix_competitor_discovery_candidates_research_validation",
        "competitor_discovery_candidates",
        ["research_run_id", "validation_status"],
    )
    op.create_index(
        "ix_competitor_discovery_candidates_discovery_run_id",
        "competitor_discovery_candidates",
        ["discovery_run_id"],
    )
    op.create_index(
        "ix_competitor_discovery_candidates_competitor_id",
        "competitor_discovery_candidates",
        ["competitor_id"],
    )
    op.create_index(
        "uq_competitor_discovery_candidates_research_domain",
        "competitor_discovery_candidates",
        ["research_run_id", "domain"],
        unique=True,
        postgresql_where=sa.text("domain IS NOT NULL"),
    )

    op.create_table(
        "competitor_discovery_candidate_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=True),
        sa.Column("source_snippet", sa.Text(), nullable=True),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("provider_result_id", sa.String(length=255), nullable=True),
        sa.Column("provider_rank", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["competitor_discovery_candidates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "canonical_url"),
    )


def downgrade() -> None:
    op.drop_table("competitor_discovery_candidate_sources")
    op.drop_index(
        "uq_competitor_discovery_candidates_research_domain",
        table_name="competitor_discovery_candidates",
    )
    op.drop_index(
        "ix_competitor_discovery_candidates_competitor_id",
        table_name="competitor_discovery_candidates",
    )
    op.drop_index(
        "ix_competitor_discovery_candidates_discovery_run_id",
        table_name="competitor_discovery_candidates",
    )
    op.drop_index(
        "ix_competitor_discovery_candidates_research_validation",
        table_name="competitor_discovery_candidates",
    )
    op.drop_table("competitor_discovery_candidates")
    op.drop_index(
        "ix_competitor_discovery_runs_research_created",
        table_name="competitor_discovery_runs",
    )
    op.drop_table("competitor_discovery_runs")
