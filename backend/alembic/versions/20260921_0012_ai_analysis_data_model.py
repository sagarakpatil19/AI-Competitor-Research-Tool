"""Create M12 AI analysis data model.

Revision ID: 20260921_0012
Revises: 20260921_0011
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0012"
down_revision: Union[str, Sequence[str], None] = "20260921_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_run_id", sa.Integer(), nullable=False),
        sa.Column("competitor_research_id", sa.Integer(), nullable=True),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("prompt_version", sa.String(length=100), nullable=False),
        sa.Column("contract_version", sa.String(length=100), nullable=False),
        sa.Column("input_snapshot_hash", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competitor_research_id"], ["competitor_research.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("scope IN ('competitor', 'research_run')", name="ck_ai_analyses_scope"),
        sa.CheckConstraint(
            "(scope = 'competitor' AND competitor_research_id IS NOT NULL) OR "
            "(scope = 'research_run' AND competitor_research_id IS NULL)",
            name="ck_ai_analyses_scope_competitor_research",
        ),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed')", name="ck_ai_analyses_status"),
    )
    op.create_index("ix_ai_analyses_research_run_id", "ai_analyses", ["research_run_id"])
    op.create_index("ix_ai_analyses_competitor_research_id", "ai_analyses", ["competitor_research_id"])
    op.create_index("ix_ai_analyses_research_run_created", "ai_analyses", ["research_run_id", "created_at"])

    op.create_table(
        "ai_analysis_input_facts",
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("fact_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["ai_analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fact_id"], ["competitor_research_facts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("analysis_id", "fact_id"),
        sa.UniqueConstraint("analysis_id", "fact_id", name="uq_ai_analysis_input_facts_analysis_fact"),
    )
    op.create_index("ix_ai_analysis_input_facts_fact_id", "ai_analysis_input_facts", ["fact_id"])

    op.create_table(
        "ai_analysis_input_evidence",
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("normalized_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["ai_analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["competitor_evidence.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("analysis_id", "evidence_id"),
        sa.UniqueConstraint("analysis_id", "evidence_id", name="uq_ai_analysis_input_evidence_analysis_evidence"),
    )
    op.create_index("ix_ai_analysis_input_evidence_evidence_id", "ai_analysis_input_evidence", ["evidence_id"])

    op.create_table(
        "ai_statements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("statement_type", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("support_status", sa.String(length=32), nullable=False),
        sa.Column("competitor_research_id", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["ai_analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competitor_research_id"], ["competitor_research.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "statement_type IN ('observation', 'feedback_insight', 'conflict', 'evidence_gap')",
            name="ck_ai_statements_statement_type",
        ),
        sa.CheckConstraint(
            "support_status IN ('supported', 'partially_supported', 'conflicting', 'insufficient_evidence')",
            name="ck_ai_statements_support_status",
        ),
    )
    op.create_index("ix_ai_statements_analysis_id", "ai_statements", ["analysis_id"])
    op.create_index("ix_ai_statements_competitor_research_id", "ai_statements", ["competitor_research_id"])

    op.create_table(
        "ai_statement_facts",
        sa.Column("statement_id", sa.Integer(), nullable=False),
        sa.Column("fact_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["statement_id"], ["ai_statements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fact_id"], ["competitor_research_facts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("statement_id", "fact_id"),
        sa.UniqueConstraint("statement_id", "fact_id", name="uq_ai_statement_facts_statement_fact"),
        sa.CheckConstraint("role IN ('supports', 'contradicts', 'context')", name="ck_ai_statement_facts_role"),
    )
    op.create_index("ix_ai_statement_facts_fact_id", "ai_statement_facts", ["fact_id"])

    op.create_table(
        "ai_statement_evidence",
        sa.Column("statement_id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("citation_excerpt", sa.Text(), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["statement_id"], ["ai_statements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["competitor_evidence.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("statement_id", "evidence_id"),
        sa.UniqueConstraint("statement_id", "evidence_id", name="uq_ai_statement_evidence_statement_evidence"),
        sa.CheckConstraint(
            "role IN ('supports', 'contradicts', 'quotes', 'context')",
            name="ck_ai_statement_evidence_role",
        ),
    )
    op.create_index("ix_ai_statement_evidence_evidence_id", "ai_statement_evidence", ["evidence_id"])

    op.create_table(
        "ai_comparisons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("comparison_type", sa.String(length=32), nullable=False),
        sa.Column("dimension", sa.String(length=100), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("support_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["ai_analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "support_status IN ('supported', 'partially_supported', 'conflicting', 'insufficient_evidence')",
            name="ck_ai_comparisons_support_status",
        ),
    )
    op.create_index("ix_ai_comparisons_analysis_id", "ai_comparisons", ["analysis_id"])

    op.create_table(
        "ai_comparison_competitors",
        sa.Column("comparison_id", sa.Integer(), nullable=False),
        sa.Column("competitor_research_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["comparison_id"], ["ai_comparisons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["competitor_research_id"], ["competitor_research.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("comparison_id", "competitor_research_id"),
        sa.UniqueConstraint(
            "comparison_id",
            "competitor_research_id",
            name="uq_ai_comparison_competitors_comparison_competitor",
        ),
        sa.CheckConstraint(
            "role IN ('subject', 'baseline', 'compared')",
            name="ck_ai_comparison_competitors_role",
        ),
    )
    op.create_index(
        "ix_ai_comparison_competitors_competitor_research_id",
        "ai_comparison_competitors",
        ["competitor_research_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_comparison_competitors_competitor_research_id", table_name="ai_comparison_competitors")
    op.drop_table("ai_comparison_competitors")
    op.drop_index("ix_ai_comparisons_analysis_id", table_name="ai_comparisons")
    op.drop_table("ai_comparisons")
    op.drop_index("ix_ai_statement_evidence_evidence_id", table_name="ai_statement_evidence")
    op.drop_table("ai_statement_evidence")
    op.drop_index("ix_ai_statement_facts_fact_id", table_name="ai_statement_facts")
    op.drop_table("ai_statement_facts")
    op.drop_index("ix_ai_statements_competitor_research_id", table_name="ai_statements")
    op.drop_index("ix_ai_statements_analysis_id", table_name="ai_statements")
    op.drop_table("ai_statements")
    op.drop_index("ix_ai_analysis_input_evidence_evidence_id", table_name="ai_analysis_input_evidence")
    op.drop_table("ai_analysis_input_evidence")
    op.drop_index("ix_ai_analysis_input_facts_fact_id", table_name="ai_analysis_input_facts")
    op.drop_table("ai_analysis_input_facts")
    op.drop_index("ix_ai_analyses_research_run_created", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_competitor_research_id", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_research_run_id", table_name="ai_analyses")
    op.drop_table("ai_analyses")
