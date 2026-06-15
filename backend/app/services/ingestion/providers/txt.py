"""
TXT provider: plain text extraction with encoding detection (UTF-8, fallback).
No structure; single body block implied.
"""

from pathlib import Path

from app.services.ingestion.providers.base import DocumentExtractorProvider
from app.services.ingestion.types import RawExtractionResult


class TxtProvider(DocumentExtractorProvider):
    """Extract text from plain .txt files with UTF-8 preferred and fallback."""

    def extract(self, file_path: Path, mime_type: str, progress_callback=None) -> RawExtractionResult:
        """
        Read file as text. Tries UTF-8 first, then falls back to latin-1 to avoid decode errors.
        """
        if not file_path.exists():
            return RawExtractionResult(
                raw_text="",
                error=f"File not found: {file_path}",
            )
        try:
            raw_bytes = file_path.read_bytes()
        except OSError as e:
            return RawExtractionResult(raw_text="", error=f"Cannot read file: {e}")
        if not raw_bytes:
            return RawExtractionResult(raw_text="", warnings=["File is empty"])
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                raw_text = raw_bytes.decode(encoding)
                return RawExtractionResult(raw_text=raw_text)
            except UnicodeDecodeError:
                continue
        return RawExtractionResult(
            raw_text="",
            error="Could not decode file with UTF-8, UTF-8-sig, latin-1, or cp1252",
        )
