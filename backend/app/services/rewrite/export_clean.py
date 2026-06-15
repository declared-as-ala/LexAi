"""Normalize contract text before PDF/DOCX export (preamble removal, typography)."""

from __future__ import annotations

import unicodedata


def strip_export_preamble(text: str) -> str:
    """
    Remove common internal QA / test blocks that precede the real contract body.

    Heuristics only affect text that clearly contains a checklist before a contract heading.
    """
    t = text.strip()
    if not t:
        return t

    lines = t.splitlines()
    if lines and lines[0].strip().endswith(".pdf") and len(lines[0].strip()) < 160:
        t = "\n".join(lines[1:]).strip()

    lower = t.lower()
    if "checklist" in lower and "contrat de prestation" in lower:
        idx = lower.find("contrat de prestation")
        if idx > 0:
            t = t[idx:].lstrip()

    if "ne pas utiliser en production" in lower and "contrat de prestation" in lower:
        idx = lower.find("contrat de prestation")
        if idx > 0:
            t = t[idx:].lstrip()

    return t


def normalize_unicode_for_export(text: str) -> str:
    """NFC normalization; map uncommon spaces to regular space."""
    t = unicodedata.normalize("NFC", text)
    t = t.replace("\u00a0", " ").replace("\u2009", " ").replace("\u202f", " ")
    return t


def display_title_from_filename(name: str) -> str:
    """Avoid repeating raw upload filename as the document title."""
    n = (name or "").strip()
    if n.lower().endswith(".pdf"):
        n = n[:-4]
    if n.lower().endswith(".docx"):
        n = n[:-5]
    return n or "Contrat"


def prepare_export_body(text: str) -> str:
    """Strip internal notes and normalize Unicode for export."""
    return normalize_unicode_for_export(strip_export_preamble(text))
