"""Rewrite session, per-recommendation decisions, and export artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.document import Document
    from app.db.models.recommendation import Recommendation


REWRITE_STATUS_DRAFT = "draft"
REWRITE_STATUS_FINALIZED = "finalized"

DECISION_PENDING = "pending"
DECISION_ACCEPTED = "accepted"
DECISION_REJECTED = "rejected"
DECISION_KEEP_ORIGINAL = "keep_original"

EXPORT_KIND_DOCX = "docx"
EXPORT_KIND_PDF = "pdf"


class RewriteSession(Base):
    __tablename__ = "rewrite_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=REWRITE_STATUS_DRAFT, index=True)
    final_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    document: Mapped["Document"] = relationship("Document")  # type: ignore[name-defined]
    decisions: Mapped[list["RewriteClauseDecision"]] = relationship(
        "RewriteClauseDecision", back_populates="session", cascade="all, delete-orphan"
    )
    exports: Mapped[list["RewriteExport"]] = relationship(
        "RewriteExport", back_populates="session", cascade="all, delete-orphan"
    )


class RewriteClauseDecision(Base):
    """One row per recommendation in a session (review accept/reject/keep)."""

    __tablename__ = "rewrite_clause_decisions"
    __table_args__ = (UniqueConstraint("session_id", "recommendation_id", name="uq_rewrite_decision_rec"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rewrite_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False, default=DECISION_PENDING)

    session: Mapped["RewriteSession"] = relationship("RewriteSession", back_populates="decisions")
    recommendation: Mapped["Recommendation"] = relationship("Recommendation")  # type: ignore[name-defined]


class RewriteExport(Base):
    __tablename__ = "rewrite_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rewrite_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["RewriteSession"] = relationship("RewriteSession", back_populates="exports")
