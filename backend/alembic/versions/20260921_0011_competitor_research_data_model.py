"""Create repeatable competitor research data model.

Revision ID: 20260921_0011
Revises: 20260921_0010
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0011"
down_revision: Union[str, Sequence[str], None] = "20260921_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "competitor_research_competitor_id_key",
        "competitor_research",
        type_="unique",
    )
    op.add_column(
        "competitor_research",
        sa.Column("research_run_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "competitor_research",
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
    )
    op.add_column(
        "competitor_research",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "competitor_research",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("competitor_research", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_competitor_research_research_run_id",
        "competitor_research",
        "research_runs",
        ["research_run_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        sa.text(
            "UPDATE competitor_research AS cr "
            "SET research_run_id = c.research_run_id "
            "FROM competitors AS c "
            "WHERE cr.competitor_id = c.id"
        )
    )
    remaining_unassigned = op.get_bind().execute(
        sa.text(
            "SELECT COUNT(*) "
            "FROM competitor_research "
            "WHERE research_run_id IS NULL"
        )
    ).scalar_one()
    if remaining_unassigned:
        raise RuntimeError(
            "Legacy competitor_research rows cannot be assigned to a research run "
            "because their associated competitor has no research_run_id. "
            f"Rows remaining: {remaining_unassigned}."
        )
    op.alter_column("competitor_research", "research_run_id", nullable=False)
    op.create_index(
        "ix_competitor_research_competitor_created",
        "competitor_research",
        ["competitor_id", "created_at"],
    )
    op.create_index(
        "ix_competitor_research_research_run_id",
        "competitor_research",
        ["research_run_id"],
    )
    op.create_check_constraint(
        "ck_competitor_research_status",
        "competitor_research",
        "status IN ('pending', 'collecting', 'structuring', 'completed', 'failed')",
    )

    op.create_table(
        "competitor_research_facts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competitor_research_id", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=32), nullable=False),
        sa.Column("fact_type", sa.String(length=100), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_numeric", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("unit", sa.String(length=100), nullable=True),
        sa.Column("period", sa.String(length=100), nullable=True),
        sa.Column("normalized_key", sa.String(length=1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["competitor_research_id"],
            ["competitor_research.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "competitor_research_id",
            "normalized_key",
            name="uq_competitor_research_facts_research_key",
        ),
        sa.CheckConstraint(
            "section IN ('company_overview', 'products', 'features', 'pricing', 'target_audience', 'customer_feedback')",
            name="ck_competitor_research_facts_section",
        ),
    )
    op.create_index(
        "ix_competitor_research_facts_competitor_research_id",
        "competitor_research_facts",
        ["competitor_research_id"],
    )
    op.create_index(
        "ix_competitor_research_facts_research_section",
        "competitor_research_facts",
        ["competitor_research_id", "section"],
    )

    op.create_table(
        "competitor_research_fact_evidence",
        sa.Column("fact_id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("citation_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["fact_id"],
            ["competitor_research_facts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["competitor_evidence.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("fact_id", "evidence_id"),
        sa.UniqueConstraint("fact_id", "evidence_id", name="uq_competitor_research_fact_evidence"),
    )
    op.create_index(
        "ix_competitor_research_fact_evidence_evidence_id",
        "competitor_research_fact_evidence",
        ["evidence_id"],
    )

    op.create_table(
        "competitor_research_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competitor_research_id", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("fact_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["competitor_research_id"],
            ["competitor_research.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "competitor_research_id",
            "section",
            name="uq_competitor_research_sections_research_section",
        ),
        sa.CheckConstraint(
            "section IN ('company_overview', 'products', 'features', 'pricing', 'target_audience', 'customer_feedback')",
            name="ck_competitor_research_sections_section",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'collected', 'structured', 'no_evidence', 'collection_failed', 'not_applicable')",
            name="ck_competitor_research_sections_status",
        ),
    )
    op.create_index(
        "ix_competitor_research_sections_competitor_research_id",
        "competitor_research_sections",
        ["competitor_research_id"],
    )
    op.create_index(
        "ix_competitor_research_sections_research_status",
        "competitor_research_sections",
        ["competitor_research_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_competitor_research_sections_research_status",
        table_name="competitor_research_sections",
    )
    op.drop_index(
        "ix_competitor_research_sections_competitor_research_id",
        table_name="competitor_research_sections",
    )
    op.drop_table("competitor_research_sections")
    op.drop_index(
        "ix_competitor_research_fact_evidence_evidence_id",
        table_name="competitor_research_fact_evidence",
    )
    op.drop_table("competitor_research_fact_evidence")
    op.drop_index(
        "ix_competitor_research_facts_research_section",
        table_name="competitor_research_facts",
    )
    op.drop_index(
        "ix_competitor_research_facts_competitor_research_id",
        table_name="competitor_research_facts",
    )
    op.drop_table("competitor_research_facts")
    op.drop_constraint("ck_competitor_research_status", "competitor_research", type_="check")
    op.drop_index("ix_competitor_research_research_run_id", table_name="competitor_research")
    op.drop_index("ix_competitor_research_competitor_created", table_name="competitor_research")
    op.drop_constraint(
        "fk_competitor_research_research_run_id",
        "competitor_research",
        type_="foreignkey",
    )
    op.drop_column("competitor_research", "failure_reason")
    op.drop_column("competitor_research", "completed_at")
    op.drop_column("competitor_research", "started_at")
    op.drop_column("competitor_research", "status")
    op.drop_column("competitor_research", "research_run_id")
    op.create_unique_constraint(
        "competitor_research_competitor_id_key",
        "competitor_research",
        ["competitor_id"],
    )
