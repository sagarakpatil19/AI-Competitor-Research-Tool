from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorResearchFactEvidence(Base):
    __tablename__ = "competitor_research_fact_evidence"
    __table_args__ = (UniqueConstraint("fact_id", "evidence_id"),)

    fact_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_research_facts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_evidence.id", ondelete="CASCADE"),
        primary_key=True,
    )
    citation_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    fact: Mapped["CompetitorResearchFact"] = relationship(back_populates="evidence_links")
    evidence: Mapped["CompetitorEvidence"] = relationship(back_populates="fact_links")
