"""PDF export via PyMuPDF with embedded Unicode fonts (French / accents)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import fitz

from app.services.rewrite.export_clean import prepare_export_body

# System fallbacks when pymupdf-fonts is not installed (Docker/Linux often has DejaVu).
_FONT_PATH_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/Library/Fonts/Arial.ttf",
)


def _load_body_font() -> fitz.Font:
    try:
        return fitz.Font("figo")
    except Exception:
        pass
    for path in _FONT_PATH_CANDIDATES:
        p = Path(path)
        if p.is_file():
            return fitz.Font(fontfile=str(p))
    raise RuntimeError(
        "No suitable TTF for PDF export: install pymupdf-fonts or add a system font "
        "(e.g. DejaVu Sans on Linux, Arial on Windows)."
    )


def _load_title_font(body: fitz.Font) -> fitz.Font:
    try:
        return fitz.Font("figbo")
    except Exception:
        return body


def _split_pages(body: str, max_chars: int = 3400) -> list[str]:
    """Split on blank-line boundaries to avoid breaking mid-paragraph when possible."""
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not paras:
        return [""]
    pages: list[str] = []
    buf: list[str] = []
    n = 0
    for p in paras:
        add_len = len(p) + (2 if buf else 0)
        if buf and n + add_len > max_chars:
            pages.append("\n\n".join(buf))
            buf = [p]
            n = len(p)
        else:
            buf.append(p)
            n += add_len
    if buf:
        pages.append("\n\n".join(buf))
    return pages


def build_pdf_bytes(
    display_title: str,
    body_text: str,
    *,
    export_date: str | None = None,
) -> bytes:
    """
    Build a multi-page A4 PDF with proper UTF-8 coverage (embedded TTF).

    Each page: header (title + date), body, footer (Page i / n).
    """
    when = export_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = prepare_export_body(body_text)
    body_font = _load_body_font()
    title_font = _load_title_font(body_font)

    font_body = "LexBody"
    font_title = "LexTitle"
    page_w, page_h = 595.0, 842.0
    margin_x = 56.0
    header_top = 20.0
    header_bottom = 46.0
    footer_top = page_h - 38.0
    footer_bottom = page_h - 12.0
    line_height = 1.38
    body_size = 11.0
    title_size = 11.0
    footer_size = 9.0

    doc = fitz.open()
    chunks = _split_pages(body, max_chars=3400)
    n_pages = max(len(chunks), 1)

    for i, chunk in enumerate(chunks):
        page = doc.new_page(width=page_w, height=page_h)
        page.insert_font(fontname=font_body, fontbuffer=body_font.buffer)
        page.insert_font(fontname=font_title, fontbuffer=title_font.buffer)

        title_line = (display_title.strip() or "Contrat") + "  ·  " + when
        hdr = fitz.Rect(margin_x, header_top, page_w - margin_x, header_bottom)
        page.insert_textbox(
            hdr,
            title_line,
            fontname=font_title,
            fontsize=title_size,
            align=fitz.TEXT_ALIGN_LEFT,
            lineheight=1.15,
        )

        body_rect = fitz.Rect(margin_x, header_bottom + 4, page_w - margin_x, footer_top - 4)
        page.insert_textbox(
            body_rect,
            chunk,
            fontname=font_body,
            fontsize=body_size,
            align=fitz.TEXT_ALIGN_LEFT,
            lineheight=line_height,
        )

        ftr = fitz.Rect(margin_x, footer_top, page_w - margin_x, footer_bottom)
        page.insert_textbox(
            ftr,
            f"Page {i + 1} / {n_pages}",
            fontname=font_body,
            fontsize=footer_size,
            align=fitz.TEXT_ALIGN_CENTER,
            color=(0.35, 0.35, 0.35),
        )

    out = doc.tobytes(deflate=True, garbage=3, clean=True)
    doc.close()
    return out
