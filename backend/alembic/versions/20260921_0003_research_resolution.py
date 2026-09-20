"""Add deterministic research input resolution fields.

Revision ID: 20260921_0003
Revises: 20260920_0002
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0003"
down_revision: Union[str, Sequence[str], None] = "20260920_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


research_input_type = sa.Enum(
    "url",
    "domain",
    "company_name",
    name="research_input_type",
)


def upgrade() -> None:
    research_input_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "research_runs",
        sa.Column("input_type", research_input_type, nullable=True),
    )
    op.add_column(
        "research_runs",
        sa.Column("resolved_domain", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("research_runs", "resolved_domain")
    op.drop_column("research_runs", "input_type")
    research_input_type.drop(op.get_bind(), checkfirst=True)