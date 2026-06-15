"""Extractor Agent orchestration: provider -> normalize -> persist."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import (
    STAGE_NORMALIZING,
    STAGE_PERSISTING,
    STAGE_SELECTING_PROVIDER,
    STATUS_EXTRACTED,
)
from app.core.logging import get_logger
from app.db.models.document import Extraction
from app.services.ingestion.progress import DocumentProgressService
from app.services.ingestion.normalizer import normalize
from app.services.ingestion.providers import get_provider
from app.services.ingestion.types import DocumentMetadata, ExtractionArtifact, RawExtractionResult

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = get_logger(__name__)


class ExtractorService:
    """Runs extraction pipeline and optionally persists results."""

    def run(
        self,
        document_id: int,
        file_path: str | Path,
        mime_type: str,
        filename: str,
        size_bytes: int = 0,
        page_count: int | None = None,
        session: Session | None = None,
    ) -> ExtractionArtifact:
        file_path = Path(file_path)
        metadata = DocumentMetadata(
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            page_count=page_count,
        )
        errors: list[str] = []
        progress = DocumentProgressService(session) if session is not None else None

        try:
            if progress is not None:
                progress.extracting(
                    document_id,
                    STAGE_SELECTING_PROVIDER,
                    "Selecting extraction provider",
                )
            provider = get_provider(mime_type)
        except ValueError as exc:
            errors.append(str(exc))
            if session:
                self._persist_error(session, document_id, None, str(exc))
                progress.failed(document_id, str(exc))
            return ExtractionArtifact(document_metadata=metadata, errors=errors)

        logger.info(
            "extractor_provider_selected",
            extra={
                "extra": {
                    "document_id": document_id,
                    "provider": provider.__class__.__name__,
                    "mime_type": mime_type,
                }
            },
        )
        if progress is not None:
            extension = file_path.suffix.lower().lstrip(".") or mime_type
            progress.extracting(
                document_id,
                "extracting",
                f"Reading {extension.upper()} content",
                35,
            )
        raw: RawExtractionResult = provider.extract(
            file_path,
            mime_type,
            progress_callback=(
                lambda stage, percent, message: progress.extracting(document_id, stage, message, percent)
            )
            if progress is not None
            else None,
        )
        if raw.error:
            errors.append(raw.error)
            if session:
                self._persist_error(session, document_id, raw.raw_text, raw.error)
                progress.failed(document_id, raw.error)
            return ExtractionArtifact(
                document_metadata=metadata,
                raw_text=raw.raw_text or "",
                normalized_text="",
                structure=raw.structure,
                page_metadata=raw.page_metadata,
                warnings=raw.warnings,
                errors=errors,
            )

        if progress is not None:
            progress.extracting(document_id, STAGE_NORMALIZING, "Normalizing extracted text")
        normalized = normalize(raw)
        if session:
            progress.extracting(document_id, STAGE_PERSISTING, "Saving extraction results")
            self._persist_success(
                session=session,
                document_id=document_id,
                raw_text=raw.raw_text or "",
                normalized_text=normalized.normalized_text,
                structure=raw.structure,
                page_metadata=raw.page_metadata,
                warnings=normalized.warnings,
            )
            progress.completed(document_id)

        logger.info(
            "extraction_completed",
            extra={
                "extra": {
                    "document_id": document_id,
                    "mime_type": mime_type,
                    "status": STATUS_EXTRACTED,
                    "warning_count": len(normalized.warnings),
                }
            },
        )
        return ExtractionArtifact(
            document_metadata=metadata,
            raw_text=raw.raw_text or "",
            normalized_text=normalized.normalized_text,
            structure=raw.structure,
            page_metadata=raw.page_metadata,
            warnings=normalized.warnings,
            errors=errors,
        )

    def _persist_error(self, session: Session, document_id: int, raw_text: str | None, error_message: str) -> None:
        extraction = Extraction(
            document_id=document_id,
            raw_text=raw_text or "",
            normalized_text="",
            error_message=error_message,
        )
        session.add(extraction)
        session.commit()

    def _persist_success(
        self,
        session: Session,
        document_id: int,
        raw_text: str,
        normalized_text: str,
        structure: dict | None,
        page_metadata: list[dict] | None,
        warnings: list[str],
    ) -> None:
        extraction = Extraction(document_id=document_id, raw_text=raw_text, normalized_text=normalized_text)
        extraction.set_structure(structure)
        extraction.set_page_metadata(page_metadata)
        extraction.set_warnings(warnings)
        session.add(extraction)
        session.commit()

