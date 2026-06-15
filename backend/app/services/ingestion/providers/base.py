"""
Base interface for document extraction providers (PDF, DOCX, TXT, HTML, OCR).

Each provider implements extract(file_path, mime_type) -> RawExtractionResult.
Unknown or unsupported types must raise or return a clear error, not silent fallback.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

from app.services.ingestion.types import RawExtractionResult

ProgressCallback = Callable[[str, int | None, str], None]


class DocumentExtractorProvider(ABC):
    """
    Abstract base class for document text extraction.
    Implementations: PDF, DOCX, TXT, HTML; OCR is a stub for later.
    """

    @abstractmethod
    def extract(
        self,
        file_path: Path,
        mime_type: str,
        progress_callback: ProgressCallback | None = None,
    ) -> RawExtractionResult:
        """
        Extract raw text and optional structure from the file.

        :param file_path: Path to the stored file.
        :param mime_type: MIME type (e.g. application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document).
        :param progress_callback: Optional callback to report stage-specific progress updates.
        :return: RawExtractionResult with raw_text, optional structure/page_metadata, warnings, or error.
        """
        ...
