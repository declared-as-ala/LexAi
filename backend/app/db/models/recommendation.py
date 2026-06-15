"""Recommendation DB model for Agent 4 output."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    violation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    clause_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    violation_rule_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    framework: Mapped[str | None] = mapped_column(String(32), nullable=True)
    article: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issue_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rewritten_clause: Mapped[str | None] = mapped_column(Text, nullable=True)
    legal_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship("Document")  # type: ignore[name-defined]
