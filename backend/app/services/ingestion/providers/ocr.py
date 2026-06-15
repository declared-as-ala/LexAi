"""
OCR provider — Tesseract via pytesseract + Pillow.
Handles JPG, PNG, TIFF, BMP, and WebP images.
Also used as fallback for scanned PDFs detected by PdfProvider.

Requires:
  pip install pytesseract Pillow
  apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-ara  (Linux/Docker)
  brew install tesseract  (macOS)
  https://github.com/UB-Mannheim/tesseract/wiki  (Windows)
"""

from __future__ import annotations

import re
from pathlib import Path

from app.services.ingestion.providers.base import DocumentExtractorProvider
from app.services.ingestion.types import RawExtractionResult

# Languages passed to Tesseract — French + English + Arabic
_TESSERACT_LANG = "fra+eng+ara"


def _clean_ocr_text(text: str) -> str:
    """Remove common OCR noise: stray control chars, excessive whitespace."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    # Collapse runs of 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces within a line
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


class OcrProvider(DocumentExtractorProvider):
    """
    Extract text from raster images (JPG, PNG, TIFF…) via Tesseract OCR.
    Lazy-imports pytesseract and Pillow so the server starts even if they
    are not installed — the error is surfaced clearly at extraction time.
    """

    def extract(
        self,
        file_path: Path,
        mime_type: str,
        progress_callback=None,
    ) -> RawExtractionResult:
        if not file_path.exists():
            return RawExtractionResult(raw_text="", error=f"File not found: {file_path}")

        try:
            from PIL import Image  # type: ignore[import]
        except ImportError:
            return RawExtractionResult(
                raw_text="",
                error="Pillow is not installed. Run: pip install Pillow",
            )

        try:
            import pytesseract  # type: ignore[import]
        except ImportError:
            return RawExtractionResult(
                raw_text="",
                error=(
                    "pytesseract is not installed. Run: pip install pytesseract\n"
                    "Also install Tesseract binary: "
                    "apt-get install tesseract-ocr tesseract-ocr-fra (Linux) | "
                    "brew install tesseract (macOS)"
                ),
            )

        if progress_callback:
            progress_callback("extracting", 20, "Opening image for OCR…")

        try:
            img = Image.open(file_path)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
        except Exception as exc:
            return RawExtractionResult(
                raw_text="", error=f"Cannot open image: {exc}"
            )

        if progress_callback:
            progress_callback("extracting", 45, "Running Tesseract OCR…")

        try:
            raw_text: str = pytesseract.image_to_string(img, lang=_TESSERACT_LANG)
        except pytesseract.TesseractNotFoundError:
            return RawExtractionResult(
                raw_text="",
                error=(
                    "Tesseract binary not found. Install it:\n"
                    "  Linux: apt-get install tesseract-ocr tesseract-ocr-fra\n"
                    "  macOS: brew install tesseract\n"
                    "  Windows: https://github.com/UB-Mannheim/tesseract/wiki"
                ),
            )
        except Exception as exc:
            return RawExtractionResult(
                raw_text="", error=f"Tesseract OCR failed: {exc}"
            )

        if progress_callback:
            progress_callback("extracting", 80, "Cleaning OCR output…")

        cleaned = _clean_ocr_text(raw_text)
        warnings: list[str] = []
        if len(cleaned) < 50:
            warnings.append(
                "OCR extracted very little text. The image may be low-resolution, "
                "rotated, or contain mostly non-text content."
            )

        width, height = img.size
        structure = {
            "type": "ocr",
            "source": "tesseract",
            "lang": _TESSERACT_LANG,
            "image_size": {"width": width, "height": height},
            "mime_type": mime_type,
        }

        return RawExtractionResult(
            raw_text=cleaned,
            structure=structure,
            warnings=warnings,
        )
