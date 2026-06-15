"""
ClauseSegmenter — Agent 2 submodule.
Segments normalized_text into discrete clauses using:
  1. Structure headings from Agent 1's structure_json (preferred)
  2. Regex-based article/section boundary detection
  3. Paragraph-break fallback
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns that signal the start of a new clause/article
_HEADING_PATTERNS = [
    # Article N — Title  /  Article N: Title  /  Art. N
    re.compile(r"^(article|art\.?)\s+\d+[\s\-–—:\.]+", re.IGNORECASE | re.MULTILINE),
    # Section N.  /  §N
    re.compile(r"^(section|§)\s*\d+[\.\s]", re.IGNORECASE | re.MULTILINE),
    # Numbered heading at top-level (1. or 1) followed by an uppercase word of 4+ chars to
    # avoid matching list items like "1. le Prestataire" or bullet points mid-clause)
    re.compile(r"^\d+[\.\)]\s+[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ][A-ZÀÂÉÈÊËÎÏÔÙÛÜÇa-z]{3,}", re.MULTILINE),
    # Roman numerals: I. / II. / III.
    re.compile(r"^(IX|IV|V?I{0,3}|X{0,3})\.\s+[A-Z]", re.MULTILINE),
    # ALL CAPS heading (at least 10 chars, whole line)
    re.compile(r"^[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ ]{10,}$", re.MULTILINE),
]

# Minimum clause length (chars) to keep — discard tiny fragments
_MIN_CLAUSE_CHARS = 50
# Merge paragraphs shorter than this into the previous segment
_MERGE_THRESHOLD_CHARS = 200
# Never produce more segments than this from paragraph fallback
_MAX_PARAGRAPH_SEGMENTS = 30


@dataclass
class ClauseSegment:
    clause_id: str
    text: str
    start_char: int
    end_char: int
    section_title: str | None = None
    source: str = "paragraph"   # "structure" | "regex" | "paragraph"


class ClauseSegmenter:
    """Segment normalized contract text into clause-level chunks."""

    def segment(
        self,
        normalized_text: str,
        structure_json: dict | None = None,
    ) -> list[ClauseSegment]:
        """
        Main entry point. Returns list of ClauseSegment ordered by position.
        Tries structure-based segmentation first, then regex, then paragraph fallback.
        """
        if not normalized_text or not normalized_text.strip():
            return []

        # Strategy 1: use section boundaries from Agent 1
        if structure_json and structure_json.get("sections"):
            segments = self._segment_by_structure(normalized_text, structure_json)
            if segments:
                logger.debug("clause_segmenter_strategy", extra={"extra": {"strategy": "structure", "count": len(segments)}})
                return segments

        # Strategy 2: regex heading detection
        segments = self._segment_by_regex(normalized_text)
        if segments:
            logger.debug("clause_segmenter_strategy", extra={"extra": {"strategy": "regex", "count": len(segments)}})
            return segments

        # Strategy 3: paragraph breaks
        segments = self._segment_by_paragraphs(normalized_text)
        logger.debug("clause_segmenter_strategy", extra={"extra": {"strategy": "paragraph", "count": len(segments)}})
        return segments

    # ------------------------------------------------------------------
    # Strategy 1 — structure JSON boundaries
    # ------------------------------------------------------------------
    def _segment_by_structure(
        self, text: str, structure_json: dict
    ) -> list[ClauseSegment]:
        sections = structure_json.get("sections", [])
        if not sections:
            return []

        segments: list[ClauseSegment] = []
        for i, sec in enumerate(sections):
            start = sec.get("start_char", 0)
            end = sections[i + 1].get("start_char", len(text)) if i + 1 < len(sections) else len(text)
            chunk = text[start:end].strip()
            if len(chunk) < _MIN_CLAUSE_CHARS:
                continue
            segments.append(ClauseSegment(
                clause_id=f"c-{i + 1:03d}",
                text=chunk,
                start_char=start,
                end_char=end,
                section_title=sec.get("title"),
                source="structure",
            ))
        return segments

    # ------------------------------------------------------------------
    # Strategy 2 — regex heading detection
    # ------------------------------------------------------------------
    def _segment_by_regex(self, text: str) -> list[ClauseSegment]:
        # Collect all heading match positions
        positions: list[tuple[int, str]] = []
        for pattern in _HEADING_PATTERNS:
            for m in pattern.finditer(text):
                positions.append((m.start(), m.group(0).strip()))

        if not positions:
            return []

        # Sort by position, deduplicate overlapping matches
        positions.sort(key=lambda x: x[0])
        deduped: list[tuple[int, str]] = []
        for pos, title in positions:
            if deduped and pos - deduped[-1][0] < 5:
                continue
            deduped.append((pos, title))

        segments: list[ClauseSegment] = []
        for i, (start, title) in enumerate(deduped):
            end = deduped[i + 1][0] if i + 1 < len(deduped) else len(text)
            chunk = text[start:end].strip()
            if len(chunk) < _MIN_CLAUSE_CHARS:
                continue
            segments.append(ClauseSegment(
                clause_id=f"c-{i + 1:03d}",
                text=chunk,
                start_char=start,
                end_char=end,
                section_title=title,
                source="regex",
            ))
        return segments

    # ------------------------------------------------------------------
    # Strategy 3 — paragraph breaks
    # ------------------------------------------------------------------
    def _segment_by_paragraphs(self, text: str) -> list[ClauseSegment]:
        raw_paragraphs = re.split(r"\n{2,}", text)

        # First pass: collect paragraphs with char positions
        paras: list[tuple[str, int, int]] = []
        cursor = 0
        for para in raw_paragraphs:
            stripped = para.strip()
            if len(stripped) >= _MIN_CLAUSE_CHARS:
                start = text.find(stripped, cursor)
                if start == -1:
                    start = cursor
                paras.append((stripped, start, start + len(stripped)))
                cursor = start + len(stripped)
            else:
                cursor += len(para) + 2

        if not paras:
            return []

        # Second pass: merge short paragraphs into the previous one to avoid
        # 50+ micro-segments from paragraph-heavy contracts
        merged: list[tuple[str, int, int]] = [paras[0]]
        for text_chunk, start, end in paras[1:]:
            prev_text, prev_start, prev_end = merged[-1]
            # Merge if previous segment is short or current chunk is short
            if len(prev_text) < _MERGE_THRESHOLD_CHARS or len(text_chunk) < _MERGE_THRESHOLD_CHARS:
                merged[-1] = (prev_text + "\n\n" + text_chunk, prev_start, end)
            else:
                merged.append((text_chunk, start, end))

        # Cap total segments
        if len(merged) > _MAX_PARAGRAPH_SEGMENTS:
            # Merge excess segments into the last kept segment
            kept = merged[:_MAX_PARAGRAPH_SEGMENTS - 1]
            overflow = merged[_MAX_PARAGRAPH_SEGMENTS - 1:]
            combined_text = "\n\n".join(t for t, _, _ in overflow)
            combined_start = overflow[0][1]
            combined_end = overflow[-1][2]
            kept.append((combined_text, combined_start, combined_end))
            merged = kept

        return [
            ClauseSegment(
                clause_id=f"c-{idx + 1:03d}",
                text=chunk,
                start_char=start,
                end_char=end,
                section_title=None,
                source="paragraph",
            )
            for idx, (chunk, start, end) in enumerate(merged)
        ]
