from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorDiscoveryRun(Base):
    __tablename__ = "competitor_discovery_runs"
    __table_args__ = (
        Index("ix_competitor_discovery_runs_research_created", "research_run_id", "created_at"),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'no_candidates')",
            name="ck_competitor_discovery_runs_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_run_id: Mapped[int] = mapped_column(
        ForeignKey("research_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    failure_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    research_run: Mapped["ResearchRun"] = relationship(back_populates="discovery_runs")
    candidates: Mapped[list["CompetitorDiscoveryCandidate"]] = relationship(
        back_populates="discovery_run",
        cascade="all, delete-orphan",
    )
