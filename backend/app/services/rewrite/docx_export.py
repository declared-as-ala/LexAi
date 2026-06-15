"""DOCX export for revised contract text (python-docx), legal-style layout."""

from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from typing import Any

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from app.services.rewrite.export_clean import prepare_export_body

_ARTICLE_LINE = re.compile(r"^\s*(Article\s+\d+[\s\u00a0\-–—].*)$", re.IGNORECASE)


def _highlight_paragraph_shading(paragraph, fill_hex: str = "FFF2CC") -> None:
    """Light yellow background (Word shading)."""
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill_hex)
    shd.set(qn("w:val"), "clear")
    p_pr = paragraph._element.get_or_add_pPr()
    p_pr.append(shd)


def _add_page_number_field(paragraph) -> None:
    """Insert Word PAGE field (current page number) in the paragraph's last run."""
    run = paragraph.add_run()
    r = run._element
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    r.append(fld_begin)
    r.append(instr)
    r.append(fld_sep)
    r.append(placeholder)
    r.append(fld_end)


def _changed_applied_texts(metadata: list[dict[str, Any]] | None) -> set[str]:
    if not metadata:
        return set()
    out: set[str] = set()
    for m in metadata:
        if not m.get("changed"):
            continue
        t = (m.get("applied_text") or "").strip()
        if len(t) >= 12:
            out.add(t)
    return out


def build_docx_bytes(
    display_title: str,
    body_text: str,
    revision_summary: list[str] | None = None,
    *,
    export_date: str | None = None,
    revision_metadata: list[dict[str, Any]] | None = None,
) -> bytes:
    when = export_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    pf = style.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.25
    pf.space_after = Pt(6)

    header = section.header
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.text = ""
    ht = hp.add_run((display_title.strip() or "Contrat") + "  ·  " + when)
    ht.font.name = "Times New Roman"
    ht.font.size = Pt(11)
    ht.bold = True

    footer = section.footer
    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.text = ""
    fr = fp.add_run("Page ")
    fr.font.name = "Times New Roman"
    fr.font.size = Pt(10)
    _add_page_number_field(fp)

    body = prepare_export_body(body_text)
    highlight_set = _changed_applied_texts(revision_metadata)

    for block in body.split("\n\n"):
        stripped = block.strip()
        if not stripped:
            continue
        highlight_block = any(ht and ht in stripped for ht in highlight_set)
        lines = stripped.splitlines()
        if len(lines) == 1 and _ARTICLE_LINE.match(lines[0]):
            p = doc.add_paragraph()
            run = p.add_run(lines[0].strip())
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            if highlight_block:
                _highlight_paragraph_shading(p)
            continue
        para = doc.add_paragraph()
        for j, line in enumerate(lines):
            if j > 0:
                para.add_run().add_break()
            if _ARTICLE_LINE.match(line):
                run = para.add_run(line.strip())
                run.bold = True
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
            else:
                run = para.add_run(line)
                run.font.name = "Times New Roman"
                run.font.size = Pt(12)
        if highlight_block:
            _highlight_paragraph_shading(para)

    if revision_summary:
        doc.add_page_break()
        ann = doc.add_heading("Annexe — trace des modifications", level=1)
        for r in ann.runs:
            r.font.name = "Times New Roman"
        for line in revision_summary:
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(line)
            run.font.name = "Times New Roman"
            run.font.size = Pt(10)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def revision_summary_lines(metadata: list[dict[str, Any]], max_items: int = 50) -> list[str]:
    lines: list[str] = []
    for entry in metadata[:max_items]:
        if not entry.get("changed"):
            continue
        cid = entry.get("clause_id") or "?"
        lines.append(f"{cid}: texte remplacé ({entry.get('start_char')}-{entry.get('end_char')})")
    if not lines:
        lines.append("Aucune clause modifiée dans cette version.")
    return lines
