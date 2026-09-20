"""Associate competitors with research runs.

Revision ID: 20260921_0005
Revises: 20260921_0004
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0005"
down_revision: Union[str, Sequence[str], None] = "20260921_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "competitors",
        "project_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column(
        "competitors",
        sa.Column("research_run_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "competitors",
        sa.Column("domain", sa.String(length=255), nullable=True),
    )
    op.create_foreign_key(
        "fk_competitors_research_run_id",
        "competitors",
        "research_runs",
        ["research_run_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_competitors_research_run_id",
        "competitors",
        ["research_run_id"],
    )
    op.create_unique_constraint(
        "uq_competitors_research_run_domain",
        "competitors",
        ["research_run_id", "domain"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_competitors_research_run_domain", "competitors", type_="unique")
    op.drop_index("ix_competitors_research_run_id", table_name="competitors")
    op.drop_constraint("fk_competitors_research_run_id", "competitors", type_="foreignkey")
    op.drop_column("competitors", "domain")
    op.drop_column("competitors", "research_run_id")
    op.alter_column(
        "competitors",
        "project_id",
        existing_type=sa.Integer(),
        nullable=False,
    )