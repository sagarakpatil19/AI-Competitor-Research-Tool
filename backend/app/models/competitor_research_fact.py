from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorResearchFact(Base):
    __tablename__ = "competitor_research_facts"
    __table_args__ = (
        UniqueConstraint("competitor_research_id", "normalized_key"),
        Index("ix_competitor_research_facts_research_section", "competitor_research_id", "section"),
        CheckConstraint(
            "section IN ('company_overview', 'products', 'features', 'pricing', 'target_audience', 'customer_feedback')",
            name="ck_competitor_research_facts_section",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competitor_research_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_research.id", ondelete="CASCADE"),
        nullable=False,
    )
    section: Mapped[str] = mapped_column(String(32), nullable=False)
    fact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_numeric: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    period: Mapped[str | None] = mapped_column(String(100), nullable=True)
    normalized_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    competitor_research: Mapped["CompetitorResearch"] = relationship(back_populates="facts")
    evidence_links: Mapped[list["CompetitorResearchFactEvidence"]] = relationship(
        back_populates="fact",
        cascade="all, delete-orphan",
    )
