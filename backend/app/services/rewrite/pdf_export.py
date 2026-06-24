"""PDF export via PyMuPDF — structured contract layout with heading detection."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import fitz

from app.services.rewrite.export_clean import prepare_export_body

_FONT_PATH_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "/Library/Fonts/Arial.ttf",
)


def _load_font(bold: bool = False) -> fitz.Font:
    """Load body or bold font with fallback chain."""
    if bold:
        try:
            return fitz.Font("figbo")
        except Exception:
            pass
        bold_candidates = [p for p in _FONT_PATH_CANDIDATES if "Bold" in p or "bd" in p or "bold" in p.lower()]
        for path in bold_candidates:
            p = Path(path)
            if p.is_file():
                return fitz.Font(fontfile=str(p))
    else:
        try:
            return fitz.Font("figo")
        except Exception:
            pass
    for path in _FONT_PATH_CANDIDATES:
        p = Path(path)
        if p.is_file():
            return fitz.Font(fontfile=str(p))
    raise RuntimeError("No suitable TTF font found for PDF export.")


# ── Block types ──────────────────────────────────────────────────────

BlockKind = Literal["title", "h1", "h2", "h3", "body", "list_item", "spacer"]


def _classify_line(line: str) -> BlockKind:
    s = line.strip()
    if not s:
        return "spacer"

    # ARTICLE X — primary contract headings
    if re.match(r"^(ARTICLE|CHAPITRE|TITRE|SECTION|CLAUSE)\s+\d+", s, re.IGNORECASE):
        return "h1"

    # All-caps short lines → heading
    if s.isupper() and 4 <= len(s) <= 90 and not s.startswith("-") and not s.startswith("•"):
        return "h1"

    # Numbered: "1.", "1.1.", "I.", "II." followed by text
    if re.match(r"^(\d+\.)+\d*\s+\S", s) or re.match(r"^[IVXLC]+\.\s+\S", s):
        return "h2"

    # Letter-labeled sub-articles: "a)", "b." etc.
    if re.match(r"^[a-zA-Z]\)\s+\S", s) or re.match(r"^[a-zA-Z]\.\s+\S", s):
        return "h3"

    # Lines ending with colon and short (label-style)
    if s.endswith(":") and len(s) <= 80:
        return "h3"

    # Bullet / dash list items
    if s.startswith(("- ", "– ", "• ", "* ", "· ")):
        return "list_item"

    return "body"


def _parse_blocks(text: str) -> list[tuple[BlockKind, str]]:
    """Convert raw text into (kind, text) block list."""
    blocks: list[tuple[BlockKind, str]] = []
    prev_spacer = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        kind = _classify_line(line)

        # Collapse consecutive spacers into one
        if kind == "spacer":
            if not prev_spacer and blocks:
                blocks.append(("spacer", ""))
            prev_spacer = True
            continue
        prev_spacer = False

        # Merge continuation body lines into previous body block
        if (
            kind == "body"
            and blocks
            and blocks[-1][0] == "body"
            and not blocks[-1][1].endswith((".", ":", ";", "?", "!"))
        ):
            blocks[-1] = ("body", blocks[-1][1] + " " + line.strip())
        else:
            blocks.append((kind, line.strip()))

    return blocks


# ── Rendering ────────────────────────────────────────────────────────

# Style: (font_key, size, color_rgb, left_indent, space_before, space_after)
_STYLE: dict[BlockKind, tuple[str, float, tuple, float, float, float]] = {
    "title":     ("bold", 16.0, (0.07, 0.07, 0.10), 0,    0,   10),
    "h1":        ("bold", 12.5, (0.07, 0.07, 0.10), 0,   10,    5),
    "h2":        ("bold", 11.0, (0.12, 0.18, 0.35), 4,    6,    3),
    "h3":        ("bold", 10.5, (0.22, 0.28, 0.45), 8,    4,    2),
    "body":      ("body", 10.5, (0.15, 0.15, 0.15), 0,    2,    2),
    "list_item": ("body", 10.5, (0.15, 0.15, 0.15), 12,   1,    1),
    "spacer":    ("body",  5.0, (1, 1, 1),           0,    0,    0),
}

# Separator line drawn under h1
_H1_RULE_COLOR = (0.78, 0.64, 0.21)  # gold


class _PageWriter:
    """Stateful page cursor — handles overflow/new-page automatically."""

    PAGE_W = 595.0
    PAGE_H = 842.0
    MARGIN_X = 56.0
    MARGIN_TOP = 70.0      # below header
    MARGIN_BOTTOM = 54.0   # above footer

    def __init__(self, doc: fitz.Document, font_body: fitz.Font, font_bold: fitz.Font):
        self._doc = doc
        self._fb = font_body
        self._fbd = font_bold
        self._page: fitz.Page | None = None
        self._y = 0.0
        self._page_num = 0
        self._pages: list[fitz.Page] = []

    @property
    def text_width(self) -> float:
        return self.PAGE_W - 2 * self.MARGIN_X

    @property
    def bottom_limit(self) -> float:
        return self.PAGE_H - self.MARGIN_BOTTOM

    def _new_page(self) -> None:
        self._page = self._doc.new_page(width=self.PAGE_W, height=self.PAGE_H)
        self._pages.append(self._page)
        self._page_num += 1
        self._page.insert_font(fontname="LexBody", fontbuffer=self._fb.buffer)
        self._page.insert_font(fontname="LexBold", fontbuffer=self._fbd.buffer)
        self._y = self.MARGIN_TOP

    def _ensure_page(self) -> None:
        if self._page is None:
            self._new_page()

    def _font_name(self, key: str) -> str:
        return "LexBold" if key == "bold" else "LexBody"

    def _text_height(self, text: str, size: float, indent: float) -> float:
        """Estimate rendered height for the given text block."""
        w = self.text_width - indent
        if w <= 0:
            return size * 1.4
        chars_per_line = max(1, int(w / (size * 0.52)))
        n_lines = max(1, -(-len(text) // chars_per_line))  # ceil division
        return n_lines * size * 1.4

    def draw_block(self, kind: BlockKind, text: str) -> None:
        font_key, size, color, indent, sp_before, sp_after = _STYLE[kind]
        font_name = self._font_name(font_key)

        self._ensure_page()

        h = self._text_height(text, size, indent) if kind != "spacer" else size
        total = sp_before + h + sp_after

        # Page break if not enough room
        if self._y + total > self.bottom_limit:
            self._new_page()

        self._y += sp_before

        if kind != "spacer":
            rect = fitz.Rect(
                self.MARGIN_X + indent,
                self._y,
                self.MARGIN_X + self.text_width,
                self._y + h + 4,  # small safety pad
            )
            self._page.insert_textbox(  # type: ignore[union-attr]
                rect,
                text,
                fontname=font_name,
                fontsize=size,
                color=color,
                align=fitz.TEXT_ALIGN_LEFT,
                lineheight=1.38,
            )

        self._y += h + sp_after

        # Draw gold rule under h1
        if kind == "h1":
            rule_y = self._y + 1
            self._page.draw_line(  # type: ignore[union-attr]
                fitz.Point(self.MARGIN_X, rule_y),
                fitz.Point(self.PAGE_W - self.MARGIN_X, rule_y),
                color=_H1_RULE_COLOR,
                width=0.6,
            )
            self._y += 4

    def stamp_headers_footers(self, title: str, when: str, total_pages: int) -> None:
        for i, page in enumerate(self._pages):
            # Header
            hdr = fitz.Rect(self.MARGIN_X, 14, self.PAGE_W - self.MARGIN_X, 46)
            page.insert_textbox(
                hdr,
                f"{title}  ·  {when}",
                fontname="LexBold",
                fontsize=9,
                color=(0.40, 0.32, 0.08),
                align=fitz.TEXT_ALIGN_LEFT,
                lineheight=1.2,
            )
            # Gold header rule
            page.draw_line(
                fitz.Point(self.MARGIN_X, 47),
                fitz.Point(self.PAGE_W - self.MARGIN_X, 47),
                color=_H1_RULE_COLOR,
                width=0.8,
            )
            # Footer rule
            footer_y = self.PAGE_H - self.MARGIN_BOTTOM + 8
            page.draw_line(
                fitz.Point(self.MARGIN_X, footer_y),
                fitz.Point(self.PAGE_W - self.MARGIN_X, footer_y),
                color=(0.80, 0.80, 0.80),
                width=0.4,
            )
            # Footer text
            ftr = fitz.Rect(self.MARGIN_X, footer_y + 4, self.PAGE_W - self.MARGIN_X, self.PAGE_H - 10)
            page.insert_textbox(
                ftr,
                f"Page {i + 1} / {total_pages}     —     LexAI · Contrat révisé",
                fontname="LexBody",
                fontsize=8,
                color=(0.50, 0.50, 0.50),
                align=fitz.TEXT_ALIGN_CENTER,
            )


# ── Public API ───────────────────────────────────────────────────────

def build_pdf_bytes(
    display_title: str,
    body_text: str,
    *,
    export_date: str | None = None,
) -> bytes:
    """Build a structured, multi-page A4 PDF from contract text."""
    when = export_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = prepare_export_body(body_text)

    font_body = _load_font(bold=False)
    font_bold = _load_font(bold=True)

    doc = fitz.open()
    writer = _PageWriter(doc, font_body, font_bold)

    # Document title block at top of first page
    title_text = (display_title.strip() or "Contrat Révisé").upper()
    writer.draw_block("title", title_text)
    writer.draw_block("spacer", "")

    # Parse and render all blocks
    blocks = _parse_blocks(body)
    for kind, text in blocks:
        writer.draw_block(kind, text)

    # Stamp headers/footers on every page
    writer.stamp_headers_footers(
        display_title.strip() or "Contrat Révisé",
        when,
        len(writer._pages),
    )

    out = doc.tobytes(deflate=True, garbage=3, clean=True)
    doc.close()
    return out
