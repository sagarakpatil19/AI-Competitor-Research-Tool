from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIComparison(Base):
    __tablename__ = "ai_comparisons"
    __table_args__ = (
        CheckConstraint(
            "support_status IN ('supported', 'partially_supported', 'conflicting', 'insufficient_evidence')",
            name="ck_ai_comparisons_support_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("ai_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    comparison_type: Mapped[str] = mapped_column(String(32), nullable=False)
    dimension: Mapped[str] = mapped_column(String(100), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    support_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    analysis: Mapped["AIAnalysis"] = relationship(back_populates="comparisons")
    competitors: Mapped[list["AIComparisonCompetitor"]] = relationship(back_populates="comparison", cascade="all, delete-orphan")
