from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIStatementEvidence(Base):
    __tablename__ = "ai_statement_evidence"
    __table_args__ = (
        UniqueConstraint("statement_id", "evidence_id"),
        CheckConstraint(
            "role IN ('supports', 'contradicts', 'quotes', 'context')",
            name="ck_ai_statement_evidence_role",
        ),
    )

    statement_id: Mapped[int] = mapped_column(
        ForeignKey("ai_statements.id", ondelete="CASCADE"), primary_key=True
    )
    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_evidence.id", ondelete="RESTRICT"), primary_key=True
    )
    citation_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    statement: Mapped["AIStatement"] = relationship(back_populates="evidence_links")
    evidence: Mapped["CompetitorEvidence"] = relationship(back_populates="ai_statement_links")
