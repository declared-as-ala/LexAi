"""
DOCX provider: extract paragraphs and headings via python-docx.
Builds simple structure (sections/headings) for downstream segmentation.
"""

from pathlib import Path

from app.services.ingestion.providers.base import DocumentExtractorProvider
from app.services.ingestion.types import RawExtractionResult


class DocxProvider(DocumentExtractorProvider):
    """Extract text and heading/section structure from .docx using python-docx."""

    def extract(self, file_path: Path, mime_type: str, progress_callback=None) -> RawExtractionResult:
        """
        Read DOCX paragraphs; detect headings by style; build structure and full text.
        """
        if not file_path.exists():
            return RawExtractionResult(raw_text="", error=f"File not found: {file_path}")
        try:
            from docx import Document
        except ImportError:
            return RawExtractionResult(
                raw_text="",
                error="python-docx is not installed; install with: pip install python-docx",
            )
        try:
            doc = Document(file_path)
        except Exception as e:
            return RawExtractionResult(
                raw_text="",
                error=f"Cannot open DOCX (possibly corrupt): {e}",
            )
        paragraphs: list[str] = []
        structure_blocks: list[dict] = []
        for i, para in enumerate(doc.paragraphs):
            text = (para.text or "").strip()
            if not text:
                continue
            paragraphs.append(text)
            style_name = para.style.name if para.style else ""
            is_heading = "heading" in style_name.lower()
            structure_blocks.append({
                "index": i,
                "text_preview": text[:80] + ("..." if len(text) > 80 else ""),
                "is_heading": is_heading,
                "style": style_name,
            })
        raw_text = "\n\n".join(paragraphs)
        structure = {
            "type": "docx",
            "paragraph_count": len(paragraphs),
            "blocks": structure_blocks,
        }
        return RawExtractionResult(
            raw_text=raw_text,
            structure=structure,
        )
