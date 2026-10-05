"""Enforce one competitor research execution per run and competitor.

Revision ID: 20261005_0014
Revises: 20260925_0013
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261005_0014"
down_revision: Union[str, Sequence[str], None] = "20260925_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    duplicate_rows = bind.execute(
        sa.text(
            "SELECT research_run_id, competitor_id, COUNT(*) AS row_count "
            "FROM competitor_research "
            "GROUP BY research_run_id, competitor_id "
            "HAVING COUNT(*) > 1 "
            "ORDER BY research_run_id, competitor_id"
        )
    ).fetchall()
    if duplicate_rows:
        details = ", ".join(
            f"(research_run_id={row.research_run_id}, competitor_id={row.competitor_id}, "
            f"count={row.row_count})"
            for row in duplicate_rows
        )
        raise RuntimeError(
            "Cannot add competitor research idempotency constraint because duplicate "
            f"logical executions exist: {details}. Resolve these records explicitly "
            "before rerunning this migration; no rows were deleted."
        )

    op.create_unique_constraint(
        "uq_competitor_research_run_competitor",
        "competitor_research",
        ["research_run_id", "competitor_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_competitor_research_run_competitor",
        "competitor_research",
        type_="unique",
    )
