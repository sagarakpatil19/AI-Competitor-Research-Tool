from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIAnalysisInputFact(Base):
    __tablename__ = "ai_analysis_input_facts"
    __table_args__ = (
        UniqueConstraint("analysis_id", "fact_id"),
        Index("ix_ai_analysis_input_facts_fact_id", "fact_id"),
    )

    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("ai_analyses.id", ondelete="CASCADE"), primary_key=True
    )
    fact_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_research_facts.id", ondelete="RESTRICT"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    analysis: Mapped["AIAnalysis"] = relationship(back_populates="input_facts")
    fact: Mapped["CompetitorResearchFact"] = relationship(back_populates="ai_analysis_inputs")
