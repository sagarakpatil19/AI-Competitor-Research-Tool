from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIStatement(Base):
    __tablename__ = "ai_statements"
    __table_args__ = (
        CheckConstraint(
            "statement_type IN ('observation', 'feedback_insight', 'conflict', 'evidence_gap')",
            name="ck_ai_statements_statement_type",
        ),
        CheckConstraint(
            "support_status IN ('supported', 'partially_supported', 'conflicting', 'insufficient_evidence')",
            name="ck_ai_statements_support_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("ai_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    statement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    support_status: Mapped[str] = mapped_column(String(32), nullable=False)
    competitor_research_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitor_research.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    section: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    analysis: Mapped["AIAnalysis"] = relationship(back_populates="statements")
    competitor_research: Mapped["CompetitorResearch | None"] = relationship(back_populates="ai_statements")
    fact_links: Mapped[list["AIStatementFact"]] = relationship(back_populates="statement", cascade="all, delete-orphan")
    evidence_links: Mapped[list["AIStatementEvidence"]] = relationship(back_populates="statement", cascade="all, delete-orphan")
    report_items: Mapped[list["ResearchReportSectionItem"]] = relationship(back_populates="statement")
