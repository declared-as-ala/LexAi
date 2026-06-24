"""PDF export via PyMuPDF — structured contract layout with heading detection."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import fitz

from app.services.rewrite.export_clean import prepare_export_body

_FONT_PATH_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "/Library/Fonts/Arial.ttf",
)

_BOLD_FONT_PATH_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
)


def _load_body_font() -> fitz.Font:
    try:
        return fitz.Font("figo")
    except Exception:
        pass
    for path in _FONT_PATH_CANDIDATES:
        if Path(path).is_file():
            return fitz.Font(fontfile=path)
    raise RuntimeError("No body font found. Install pymupdf-fonts or DejaVu Sans.")


def _load_bold_font(body: fitz.Font) -> fitz.Font:
    try:
        return fitz.Font("figbo")
    except Exception:
        pass
    for path in _BOLD_FONT_PATH_CANDIDATES:
        if Path(path).is_file():
            return fitz.Font(fontfile=path)
    return body  # fall back to body font if no bold available


# ── Block classification ─────────────────────────────────────────────

def _classify(line: str) -> str:
    s = line.strip()
    if not s:
        return "spacer"
    if re.match(r"^(ARTICLE|CHAPITRE|TITRE|SECTION|CLAUSE)\s+\d+", s, re.IGNORECASE):
        return "h1"
    if s.isupper() and 4 <= len(s) <= 90 and s[0] not in ("-", "•", "*"):
        return "h1"
    if re.match(r"^(\d+\.)+\d*\s+\S", s) or re.match(r"^[IVXLC]+\.\s+\S", s):
        return "h2"
    if re.match(r"^[a-zA-Z]\)\s+\S", s) or (s.endswith(":") and len(s) <= 80):
        return "h3"
    if s[:2] in ("- ", "– ", "• ", "* ", "· "):
        return "list"
    return "body"


def _parse_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    prev_space = False
    for raw in text.splitlines():
        line = raw.rstrip()
        kind = _classify(line)
        if kind == "spacer":
            if not prev_space and blocks:
                blocks.append(("spacer", ""))
            prev_space = True
            continue
        prev_space = False
        s = line.strip()
        if (
            kind == "body" and blocks and blocks[-1][0] == "body"
            and not blocks[-1][1].endswith((".", ":", ";", "?", "!"))
        ):
            blocks[-1] = ("body", blocks[-1][1] + " " + s)
        else:
            blocks.append((kind, s))
    return blocks


# ── PDF construction ─────────────────────────────────────────────────

PAGE_W = 595.0
PAGE_H = 842.0
MX = 56.0          # horizontal margin
CONTENT_W = PAGE_W - 2 * MX
TOP = 68.0         # body starts here (below header)
BOTTOM = PAGE_H - 48.0  # body ends here (above footer)

FNAME_REG = "LexR"
FNAME_BLD = "LexB"


def _new_page(doc: fitz.Document, body_buf: bytes, bold_buf: bytes) -> tuple[fitz.Page, float]:
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    page.insert_font(fontname=FNAME_REG, fontbuffer=body_buf)
    page.insert_font(fontname=FNAME_BLD, fontbuffer=bold_buf)
    return page, TOP


def _draw(page: fitz.Page, y: float, text: str, fname: str,
          size: float, color: tuple, indent: float = 0.0) -> float:
    """Draw text block at y, return new y position."""
    if not text:
        return y
    # Estimate lines needed
    chars_per_line = max(1, int((CONTENT_W - indent) / (size * 0.52)))
    n_lines = max(1, (len(text) + chars_per_line - 1) // chars_per_line)
    h = n_lines * size * 1.45 + 4
    rect = fitz.Rect(MX + indent, y, MX + CONTENT_W, y + h)
    page.insert_textbox(
        rect, text,
        fontname=fname, fontsize=size,
        color=color, align=0, lineheight=1.40,
    )
    return y + h


def build_pdf_bytes(
    display_title: str,
    body_text: str,
    *,
    export_date: str | None = None,
) -> bytes:
    when = export_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = prepare_export_body(body_text)

    body_font = _load_body_font()
    bold_font = _load_bold_font(body_font)
    body_buf = body_font.buffer
    bold_buf = bold_font.buffer

    doc = fitz.open()
    all_pages: list[fitz.Page] = []

    page, y = _new_page(doc, body_buf, bold_buf)
    all_pages.append(page)

    def need_break(needed: float) -> None:
        nonlocal page, y
        if y + needed > BOTTOM:
            page, y = _new_page(doc, body_buf, bold_buf)
            all_pages.append(page)

    # ── Document title ──
    need_break(40)
    y = _draw(page, y, (display_title or "Contrat").upper(), FNAME_BLD, 15, (0.05, 0.05, 0.10))
    y += 4
    y = _draw(page, y, f"Exporté le {when}  ·  LexAI", FNAME_REG, 9, (0.50, 0.50, 0.50))
    y += 18

    # ── Body blocks ──
    blocks = _parse_blocks(body)
    for kind, text in blocks:

        if kind == "spacer":
            y += 7
            continue

        if kind == "h1":
            y += 12
            need_break(30)
            y = _draw(page, y, text, FNAME_BLD, 12.5, (0.05, 0.05, 0.10))
            y += 5

        elif kind == "h2":
            y += 7
            need_break(24)
            y = _draw(page, y, text, FNAME_BLD, 11.0, (0.10, 0.20, 0.42), indent=6)
            y += 3

        elif kind == "h3":
            y += 5
            need_break(20)
            y = _draw(page, y, text, FNAME_BLD, 10.5, (0.20, 0.28, 0.50), indent=12)
            y += 2

        elif kind == "list":
            clean = re.sub(r"^[-–•*·]\s*", "", text)
            need_break(18)
            y = _draw(page, y, "• " + clean, FNAME_REG, 10.5, (0.12, 0.12, 0.12), indent=16)
            y += 2

        else:  # body
            lines_est = max(1, len(text) // 85 + 1)
            need_break(lines_est * 10.5 * 1.45 + 8)
            y = _draw(page, y, text, FNAME_REG, 10.5, (0.10, 0.10, 0.10))
            y += 5

    # ── Headers and footers ──
    n = len(all_pages)
    title_str = (display_title or "Contrat").strip()
    for i, pg in enumerate(all_pages):
        # Header line
        pg.insert_textbox(
            fitz.Rect(MX, 15, PAGE_W - MX, 48),
            f"{title_str}  ·  {when}",
            fontname=FNAME_BLD, fontsize=9,
            color=(0.40, 0.30, 0.05), align=0,
        )
        # Footer line
        pg.insert_textbox(
            fitz.Rect(MX, PAGE_H - 40, PAGE_W - MX, PAGE_H - 12),
            f"Page {i + 1} / {n}  —  LexAI · Contrat révisé",
            fontname=FNAME_REG, fontsize=8,
            color=(0.50, 0.50, 0.50), align=1,
        )

    out = doc.tobytes(deflate=True, garbage=3, clean=True)
    doc.close()
    return out
