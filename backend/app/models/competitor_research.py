from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorResearchStatus(str, Enum):
    PENDING = "pending"
    COLLECTING = "collecting"
    STRUCTURING = "structuring"
    COMPLETED = "completed"
    FAILED = "failed"


class CompetitorResearch(Base):
    __tablename__ = "competitor_research"
    __table_args__ = (
        Index("ix_competitor_research_competitor_created", "competitor_id", "created_at"),
        CheckConstraint(
            "status IN ('pending', 'collecting', 'structuring', 'completed', 'failed')",
            name="ck_competitor_research_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competitor_id: Mapped[int] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    research_run_id: Mapped[int] = mapped_column(
        ForeignKey("research_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompetitorResearchStatus.PENDING.value, server_default="pending"
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    products_services: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_customers: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    competitor: Mapped["Competitor"] = relationship(back_populates="research_executions")
    research_run: Mapped["ResearchRun"] = relationship(back_populates="competitor_researches")
    sections: Mapped[list["CompetitorResearchSection"]] = relationship(
        back_populates="competitor_research",
        cascade="all, delete-orphan",
    )
    facts: Mapped[list["CompetitorResearchFact"]] = relationship(
        back_populates="competitor_research",
        cascade="all, delete-orphan",
    )
    evidence: Mapped[list["CompetitorEvidence"]] = relationship(
        back_populates="competitor_research",
        cascade="all, delete-orphan",
    )
    sources: Mapped[list["CompetitorSource"]] = relationship(
        back_populates="competitor_research",
        cascade="all, delete-orphan",
    )
    ai_analyses: Mapped[list["AIAnalysis"]] = relationship(
        back_populates="competitor_research",
    )
    ai_statements: Mapped[list["AIStatement"]] = relationship(
        back_populates="competitor_research",
    )
    ai_comparison_links: Mapped[list["AIComparisonCompetitor"]] = relationship(
        back_populates="competitor_research",
    )