from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorDiscoveryCandidateSource(Base):
    __tablename__ = "competitor_discovery_candidate_sources"
    __table_args__ = (UniqueConstraint("candidate_id", "canonical_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_discovery_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_result_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    candidate: Mapped["CompetitorDiscoveryCandidate"] = relationship(back_populates="sources")
