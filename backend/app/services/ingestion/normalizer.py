"""
Phase 3: Normalize raw extraction — UTF-8, consistent whitespace, paragraph boundaries.
Warnings from raw extraction are carried over. Future: anonymization hook (interface only).
"""

import re

from app.services.ingestion.types import NormalizedExtraction, RawExtractionResult


def normalize(raw: RawExtractionResult) -> NormalizedExtraction:
    """
    Normalize raw extracted text: ensure valid UTF-8, collapse whitespace,
    and preserve paragraph boundaries (double newline). Optionally pass through structure.
    """
    text = raw.raw_text or ""
    # Replace invalid UTF-8 / replacement chars
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    text = str(text).encode("utf-8", errors="replace").decode("utf-8")
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple spaces inside a line
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse more than 2 consecutive newlines to 2 (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace and normalize empty to ""
    text = text.strip() or ""
    # Optional: carry over structure (no deep normalization for MVP)
    normalized_structure = raw.structure
    return NormalizedExtraction(
        normalized_text=text,
        normalized_structure=normalized_structure,
        warnings=list(raw.warnings),
    )
