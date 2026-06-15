"""Reusable progress updater for Agent 1 document processing."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import (
    STAGE_COMPLETED,
    STAGE_FAILED,
    STAGE_PROGRESS_DEFAULTS,
    STATUS_EXTRACTED,
    STATUS_EXTRACTING,
    STATUS_FAILED,
    STATUS_QUEUED,
)
from app.db.models.document import Document

_UNSET = object()


class DocumentProgressService:
    """Persist live progress fields for a document during extraction."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def update(
        self,
        document_id: int,
        *,
        status: str | None = None,
        stage: str | None = None,
        percent: int | None = None,
        message: str | None = None,
        last_error: str | None | object = _UNSET,
        finished: bool = False,
    ) -> Document | None:
        document = self.session.get(Document, document_id)
        if document is None:
            return None

        if status is not None:
            document.status = status
        if stage is not None:
            document.progress_stage = stage
        if percent is not None:
            document.progress_percent = max(0, min(100, percent))
        elif stage is not None and stage in STAGE_PROGRESS_DEFAULTS:
            document.progress_percent = STAGE_PROGRESS_DEFAULTS[stage]
        if message is not None:
            document.progress_message = message
        if last_error is not _UNSET:
            document.last_error = last_error
        if finished:
            document.finished_at = datetime.now(timezone.utc)
        elif status in {STATUS_QUEUED, STATUS_EXTRACTING}:
            document.finished_at = None

        self.session.commit()
        self.session.refresh(document)
        return document

    def queued(self, document_id: int, message: str = "Task queued for extraction") -> Document | None:
        return self.update(
            document_id,
            status=STATUS_QUEUED,
            stage="queued",
            message=message,
            last_error=None,
            finished=False,
        )

    def extracting(self, document_id: int, stage: str, message: str, percent: int | None = None) -> Document | None:
        return self.update(
            document_id,
            status=STATUS_EXTRACTING,
            stage=stage,
            percent=percent,
            message=message,
            last_error=None,
            finished=False,
        )

    def completed(self, document_id: int, message: str = "Extraction completed successfully") -> Document | None:
        return self.update(
            document_id,
            status=STATUS_EXTRACTED,
            stage=STAGE_COMPLETED,
            percent=STAGE_PROGRESS_DEFAULTS[STAGE_COMPLETED],
            message=message,
            last_error=None,
            finished=True,
        )

    def failed(self, document_id: int, error_message: str, percent: int | None = None) -> Document | None:
        return self.update(
            document_id,
            status=STATUS_FAILED,
            stage=STAGE_FAILED,
            percent=percent,
            message="Extraction failed",
            last_error=error_message,
            finished=True,
        )
