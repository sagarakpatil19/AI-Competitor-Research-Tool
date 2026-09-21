from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIStatementFact(Base):
    __tablename__ = "ai_statement_facts"
    __table_args__ = (
        UniqueConstraint("statement_id", "fact_id"),
        CheckConstraint(
            "role IN ('supports', 'contradicts', 'context')",
            name="ck_ai_statement_facts_role",
        ),
    )

    statement_id: Mapped[int] = mapped_column(
        ForeignKey("ai_statements.id", ondelete="CASCADE"), primary_key=True
    )
    fact_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_research_facts.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    statement: Mapped["AIStatement"] = relationship(back_populates="fact_links")
    fact: Mapped["CompetitorResearchFact"] = relationship(back_populates="ai_statement_links")
