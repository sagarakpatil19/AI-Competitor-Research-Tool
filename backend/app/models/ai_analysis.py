from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    __table_args__ = (
        Index("ix_ai_analyses_research_run_created", "research_run_id", "created_at"),
        CheckConstraint(
            "scope IN ('competitor', 'research_run')",
            name="ck_ai_analyses_scope",
        ),
        CheckConstraint(
            "(scope = 'competitor' AND competitor_research_id IS NOT NULL) OR "
            "(scope = 'research_run' AND competitor_research_id IS NULL)",
            name="ck_ai_analyses_scope_competitor_research",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_ai_analyses_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_run_id: Mapped[int] = mapped_column(
        ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    competitor_research_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitor_research.id", ondelete="CASCADE"), nullable=True, index=True
    )
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(100), nullable=False)
    input_snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    research_run: Mapped["ResearchRun"] = relationship(back_populates="ai_analyses")
    competitor_research: Mapped["CompetitorResearch | None"] = relationship(back_populates="ai_analyses")
    input_facts: Mapped[list["AIAnalysisInputFact"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    input_evidence: Mapped[list["AIAnalysisInputEvidence"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    statements: Mapped[list["AIStatement"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    comparisons: Mapped[list["AIComparison"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    reports: Mapped[list["ResearchReport"]] = relationship(back_populates="analysis")
