from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorDiscoveryCandidate(Base):
    __tablename__ = "competitor_discovery_candidates"
    __table_args__ = (
        Index(
            "ix_competitor_discovery_candidates_research_validation",
            "research_run_id",
            "validation_status",
        ),
        Index(
            "uq_competitor_discovery_candidates_research_domain",
            "research_run_id",
            "domain",
            unique=True,
            postgresql_where=text("domain IS NOT NULL"),
        ),
        CheckConstraint(
            "discovery_status IN ('received', 'normalized', 'duplicate', 'failed')",
            name="ck_competitor_discovery_candidates_discovery_status",
        ),
        CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid', 'same_company', 'rejected', 'promoted')",
            name="ck_competitor_discovery_candidates_validation_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discovery_run_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_discovery_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    research_run_id: Mapped[int] = mapped_column(
        ForeignKey("research_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    discovery_method: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_candidate_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discovery_status: Mapped[str] = mapped_column(String(32), nullable=False, default="received", server_default="received")
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    validation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitor_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    discovery_run: Mapped["CompetitorDiscoveryRun"] = relationship(back_populates="candidates")
    research_run: Mapped["ResearchRun"] = relationship(back_populates="discovery_candidates")
    competitor: Mapped["Competitor | None"] = relationship(back_populates="discovery_candidates")
    sources: Mapped[list["CompetitorDiscoveryCandidateSource"]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
