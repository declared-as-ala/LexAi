"""Smoke tests for DOCX/PDF export builders."""

from __future__ import annotations

import io
import zipfile

from app.services.rewrite.docx_export import build_docx_bytes, revision_summary_lines
from app.services.rewrite.export_clean import prepare_export_body, strip_export_preamble
from app.services.rewrite.pdf_export import build_pdf_bytes


def test_docx_magic_and_non_empty():
    raw = build_docx_bytes("Title", "Para one.\n\nPara two.", ["bullet a"])
    assert raw.startswith(b"PK")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        assert "word/document.xml" in zf.namelist()


def test_pdf_header():
    raw = build_pdf_bytes("T", "Body " * 100, export_date="2026-04-21")
    assert raw.startswith(b"%PDF")


def test_revision_summary_empty_metadata():
    lines = revision_summary_lines([])
    assert lines


def test_strip_checklist_before_contrat():
    raw = "CHECKLIST QA\nfoo\n\nCONTRAT DE PRESTATION\nsuite"
    out = strip_export_preamble(raw)
    assert out.startswith("CONTRAT DE PRESTATION")


def test_prepare_export_normalizes_nbsp():
    t = prepare_export_body("l\u00a0am\u00e9lioration")
    assert "\u00a0" not in t
    assert "l amélioration" in t
