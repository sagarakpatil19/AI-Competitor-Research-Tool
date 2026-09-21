from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIComparisonCompetitor(Base):
    __tablename__ = "ai_comparison_competitors"
    __table_args__ = (
        UniqueConstraint("comparison_id", "competitor_research_id"),
        CheckConstraint(
            "role IN ('subject', 'baseline', 'compared')",
            name="ck_ai_comparison_competitors_role",
        ),
        Index(
            "ix_ai_comparison_competitors_competitor_research_id",
            "competitor_research_id",
        ),
    )

    comparison_id: Mapped[int] = mapped_column(
        ForeignKey("ai_comparisons.id", ondelete="CASCADE"), primary_key=True
    )
    competitor_research_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_research.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    comparison: Mapped["AIComparison"] = relationship(back_populates="competitors")
    competitor_research: Mapped["CompetitorResearch"] = relationship(back_populates="ai_comparison_links")
