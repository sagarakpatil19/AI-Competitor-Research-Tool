"""Create research run table.

Revision ID: 20260920_0002
Revises: 20260920_0001
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


revision: str = "20260920_0002"
down_revision: Union[str, Sequence[str], None] = "20260920_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


research_run_status = postgresql.ENUM(
    "submitted",
    "resolving",
    "discovering",
    "validating",
    "researching",
    "analyzing",
    "completed",
    "failed",
    name="research_run_status",
    create_type=False,
)


def upgrade() -> None:
    research_run_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "research_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "input_value",
            sa.String(length=2048),
            nullable=False,
        ),
        sa.Column(
            "status",
            research_run_status,
            server_default="submitted",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("research_runs")
    research_run_status.drop(op.get_bind(), checkfirst=True)