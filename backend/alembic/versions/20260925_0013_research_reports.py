"""Create M13 research report persistence model.

Revision ID: 20260925_0013
Revises: 20260921_0012
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260925_0013"
down_revision: Union[str, Sequence[str], None] = "20260921_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REPORT_SECTIONS = (
    "company_overview",
    "products",
    "features",
    "pricing",
    "target_audience",
    "customer_feedback",
    "key_findings",
    "comparisons",
)


def upgrade() -> None:
    op.create_table(
        "research_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_run_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["analysis_id"], ["ai_analyses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("research_run_id", "version", name="uq_research_reports_run_version"),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_research_reports_status",
        ),
        sa.CheckConstraint("version > 0", name="ck_research_reports_version_positive"),
    )
    op.create_index("ix_research_reports_research_run_id", "research_reports", ["research_run_id"])
    op.create_index("ix_research_reports_analysis_id", "research_reports", ["analysis_id"])
    op.create_index(
        "ix_research_reports_research_run_created",
        "research_reports",
        ["research_run_id", "created_at"],
    )

    op.create_table(
        "research_report_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["research_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id", "section", name="uq_research_report_sections_report_section"),
        sa.UniqueConstraint("report_id", "display_order", name="uq_research_report_sections_report_order"),
        sa.CheckConstraint(
            f"section IN ({', '.join(repr(section) for section in REPORT_SECTIONS)})",
            name="ck_research_report_sections_section",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'no_content', 'failed')",
            name="ck_research_report_sections_status",
        ),
        sa.CheckConstraint("display_order >= 0", name="ck_research_report_sections_display_order_nonnegative"),
    )
    op.create_index("ix_research_report_sections_report_id", "research_report_sections", ["report_id"])
    op.create_index(
        "ix_research_report_sections_report_order",
        "research_report_sections",
        ["report_id", "display_order"],
    )

    op.create_table(
        "research_report_section_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False),
        sa.Column("ai_statement_id", sa.Integer(), nullable=True),
        sa.Column("ai_comparison_id", sa.Integer(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["section_id"], ["research_report_sections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ai_statement_id"], ["ai_statements.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ai_comparison_id"], ["ai_comparisons.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_id", "display_order", name="uq_research_report_section_items_section_order"),
        sa.CheckConstraint(
            "item_type IN ('statement', 'comparison')",
            name="ck_research_report_section_items_item_type",
        ),
        sa.CheckConstraint("display_order >= 0", name="ck_research_report_section_items_display_order_nonnegative"),
        sa.CheckConstraint(
            "(item_type = 'statement' AND ai_statement_id IS NOT NULL AND ai_comparison_id IS NULL) OR "
            "(item_type = 'comparison' AND ai_statement_id IS NULL AND ai_comparison_id IS NOT NULL)",
            name="ck_research_report_section_items_exact_reference",
        ),
    )
    op.create_index("ix_research_report_section_items_section_id", "research_report_section_items", ["section_id"])
    op.create_index("ix_research_report_section_items_ai_statement_id", "research_report_section_items", ["ai_statement_id"])
    op.create_index("ix_research_report_section_items_ai_comparison_id", "research_report_section_items", ["ai_comparison_id"])
    op.create_index(
        "ix_research_report_section_items_section_order",
        "research_report_section_items",
        ["section_id", "display_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_research_report_section_items_section_order", table_name="research_report_section_items")
    op.drop_index("ix_research_report_section_items_ai_comparison_id", table_name="research_report_section_items")
    op.drop_index("ix_research_report_section_items_ai_statement_id", table_name="research_report_section_items")
    op.drop_index("ix_research_report_section_items_section_id", table_name="research_report_section_items")
    op.drop_table("research_report_section_items")
    op.drop_index("ix_research_report_sections_report_order", table_name="research_report_sections")
    op.drop_index("ix_research_report_sections_report_id", table_name="research_report_sections")
    op.drop_table("research_report_sections")
    op.drop_index("ix_research_reports_research_run_created", table_name="research_reports")
    op.drop_index("ix_research_reports_analysis_id", table_name="research_reports")
    op.drop_index("ix_research_reports_research_run_id", table_name="research_reports")
    op.drop_table("research_reports")
