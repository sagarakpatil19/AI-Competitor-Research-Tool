from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIAnalysisInputEvidence(Base):
    __tablename__ = "ai_analysis_input_evidence"
    __table_args__ = (
        UniqueConstraint("analysis_id", "evidence_id"),
        Index("ix_ai_analysis_input_evidence_evidence_id", "evidence_id"),
    )

    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("ai_analyses.id", ondelete="CASCADE"), primary_key=True
    )
    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_evidence.id", ondelete="RESTRICT"), primary_key=True
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    normalized_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    analysis: Mapped["AIAnalysis"] = relationship(back_populates="input_evidence")
    evidence: Mapped["CompetitorEvidence"] = relationship(back_populates="ai_analysis_inputs")
