"""Document and Extraction models for the Extractor Agent."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import STAGE_QUEUED, STAGE_PROGRESS_DEFAULTS, STATUS_QUEUED
from app.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default=STATUS_QUEUED, index=True)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=STAGE_PROGRESS_DEFAULTS[STAGE_QUEUED])
    progress_stage: Mapped[str] = mapped_column(String(64), default=STAGE_QUEUED)
    progress_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    extractions: Mapped[list["Extraction"]] = relationship(
        "Extraction", back_populates="document", order_by="Extraction.id"
    )


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    normalized_text: Mapped[str] = mapped_column(Text, default="")
    structure_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship("Document", back_populates="extractions")

    def set_structure(self, value: dict[str, Any] | None) -> None:
        self.structure_json = json.dumps(value, ensure_ascii=False) if value is not None else None

    def get_structure(self) -> dict[str, Any] | None:
        if not self.structure_json:
            return None
        try:
            return json.loads(self.structure_json)
        except json.JSONDecodeError:
            return None

    def set_page_metadata(self, value: list[dict[str, Any]] | None) -> None:
        self.page_metadata_json = json.dumps(value, ensure_ascii=False) if value is not None else None

    def get_page_metadata(self) -> list[dict[str, Any]] | None:
        if not self.page_metadata_json:
            return None
        try:
            return json.loads(self.page_metadata_json)
        except json.JSONDecodeError:
            return None

    def set_warnings(self, value: list[str]) -> None:
        self.warnings = json.dumps(value, ensure_ascii=False) if value else None

    def get_warnings(self) -> list[str]:
        if not self.warnings:
            return []
        try:
            return json.loads(self.warnings)
        except json.JSONDecodeError:
            return []