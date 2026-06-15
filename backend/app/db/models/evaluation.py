"""Evaluation DB model for Agent 3 output."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )

    # Scores
    global_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    litigation_risk: Mapped[str | None] = mapped_column(String(16), nullable=True)
    lnpdp_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    gdpr_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    iso27001_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    iso9001_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Active frameworks used in scoring (JSON list)
    active_frameworks_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Violations (JSON list of Violation dicts)
    violations_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Missing mandatory clause keys (JSON list)
    missing_clauses_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Violation counts per framework (JSON dict)
    violation_counts_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship("Document")  # type: ignore[name-defined]

    def set_violations(self, violations: list[dict[str, Any]]) -> None:
        self.violations_json = json.dumps(violations, ensure_ascii=False)

    def get_violations(self) -> list[dict[str, Any]]:
        if not self.violations_json:
            return []
        try:
            return json.loads(self.violations_json)
        except json.JSONDecodeError:
            return []

    def set_missing_clauses(self, keys: list[str]) -> None:
        self.missing_clauses_json = json.dumps(keys, ensure_ascii=False)

    def get_missing_clauses(self) -> list[str]:
        if not self.missing_clauses_json:
            return []
        try:
            return json.loads(self.missing_clauses_json)
        except json.JSONDecodeError:
            return []

    def set_active_frameworks(self, frameworks: list[str]) -> None:
        self.active_frameworks_json = json.dumps(frameworks)

    def get_active_frameworks(self) -> list[str]:
        if not self.active_frameworks_json:
            return []
        try:
            return json.loads(self.active_frameworks_json)
        except json.JSONDecodeError:
            return []

    def set_violation_counts(self, counts: dict[str, int]) -> None:
        self.violation_counts_json = json.dumps(counts)

    def get_violation_counts(self) -> dict[str, int]:
        if not self.violation_counts_json:
            return {}
        try:
            return json.loads(self.violation_counts_json)
        except json.JSONDecodeError:
            return {}
