"""NLPAnalysis DB model for Agent 2 output."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class NLPAnalysis(Base):
    __tablename__ = "nlp_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    language_confidence: Mapped[float | None] = mapped_column(nullable=True)
    clause_count: Mapped[int] = mapped_column(Integer, default=0)
    clauses_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped["Document"] = relationship("Document")  # type: ignore[name-defined]

    def set_clauses(self, clauses: list[dict[str, Any]]) -> None:
        self.clauses_json = json.dumps(clauses, ensure_ascii=False)
        self.clause_count = len(clauses)

    def get_clauses(self) -> list[dict[str, Any]]:
        if not self.clauses_json:
            return []
        try:
            return json.loads(self.clauses_json)
        except json.JSONDecodeError:
            return []
