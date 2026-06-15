"""
PDF provider: text and structure extraction via PyMuPDF (fitz).
Detects likely scanned PDFs (very little text) and adds a "consider OCR" warning.
"""

from pathlib import Path

from app.services.ingestion.providers.base import DocumentExtractorProvider
from app.services.ingestion.types import RawExtractionResult

# Threshold: if extracted text has fewer than this many chars, treat as likely scanned
_SCANNED_TEXT_THRESHOLD = 50


class PdfProvider(DocumentExtractorProvider):
    """Extract text and optional page/block structure from PDF using PyMuPDF."""

    def extract(self, file_path: Path, mime_type: str, progress_callback=None) -> RawExtractionResult:
        """
        Extract text from PDF. Builds optional structure (pages, blocks) and
        page_metadata. Sets warning if document appears scanned (very little text).
        """
        if not file_path.exists():
            return RawExtractionResult(raw_text="", error=f"File not found: {file_path}")
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return RawExtractionResult(
                raw_text="",
                error="PyMuPDF (fitz) is not installed; install with: pip install pymupdf",
            )
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            return RawExtractionResult(
                raw_text="",
                error=f"Cannot open PDF (possibly password-protected or corrupt): {e}",
            )
        warnings: list[str] = []
        pages_text: list[str] = []
        page_metadata: list[dict] = []
        try:
            total_pages = len(doc)
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                pages_text.append(text)
                page_metadata.append({
                    "page": page_num + 1,
                    "char_count": len(text),
                })
                if progress_callback is not None and total_pages > 0:
                    percent = 35 + int(((page_num + 1) / total_pages) * 35)
                    progress_callback("extracting", percent, f"Extracting PDF pages ({page_num + 1}/{total_pages})")
            doc.close()
        except Exception as e:
            doc.close()
            return RawExtractionResult(
                raw_text="",
                error=f"Error while reading PDF pages: {e}",
            )
        raw_text = "\n\n".join(pages_text)
        if len(raw_text.strip()) < _SCANNED_TEXT_THRESHOLD and len(pages_text) > 0:
            warnings.append("Document may be scanned; consider using OCR for better extraction.")
        structure = {
            "type": "pdf",
            "page_count": len(pages_text),
            "pages": [{"page": i + 1, "char_count": len(t)} for i, t in enumerate(pages_text)],
        }
        return RawExtractionResult(
            raw_text=raw_text,
            structure=structure,
            page_metadata=page_metadata,
            warnings=warnings if warnings else [],
        )
