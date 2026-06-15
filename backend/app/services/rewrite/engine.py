"""Span-preserving deterministic assembly of revised contract text."""

from __future__ import annotations

from typing import Any

from app.db.models.rewrite import DECISION_ACCEPTED, DECISION_PENDING


def _rec_sort_key(rec: dict[str, Any]) -> tuple[int, int]:
    p = rec.get("priority")
    if p is None:
        p = 10_000
    return (int(p), int(rec.get("id") or 0))


def _accepted_rewrite_for_clause(
    clause_id: str,
    recommendations: list[dict[str, Any]],
    decision_by_rec_id: dict[int, str],
) -> str | None:
    """Return rewritten text to use for clause_id, or None to keep original slice."""
    candidates: list[dict[str, Any]] = []
    for rec in recommendations:
        if (rec.get("clause_id") or "") != clause_id:
            continue
        rid = rec.get("id")
        if rid is None:
            continue
        if decision_by_rec_id.get(int(rid)) != DECISION_ACCEPTED:
            continue
        rw = (rec.get("rewritten_clause") or "").strip()
        if rw:
            candidates.append(rec)
    if not candidates:
        return None
    candidates.sort(key=_rec_sort_key)
    return str(candidates[0].get("rewritten_clause") or "").strip() or None


def build_revised_text(
    normalized_text: str,
    clauses: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    decision_by_rec_id: dict[int, str],
) -> str:
    """Rebuild full text: gaps from normalized_text; each clause uses accepted rewrite or original slice."""
    n = len(normalized_text)
    sorted_clauses = clamp_clauses_for_document(clauses, n)
    parts: list[str] = []
    cursor = 0

    for c in sorted_clauses:
        start = int(c.get("start_char") or 0)
        end = int(c.get("end_char") or 0)
        cid = str(c.get("clause_id") or "")
        gap_end = min(start, n)
        if cursor < gap_end:
            parts.append(normalized_text[cursor:gap_end])
        rewrite = _accepted_rewrite_for_clause(cid, recommendations, decision_by_rec_id) if cid else None
        if rewrite is not None:
            parts.append(rewrite)
        else:
            parts.append(normalized_text[start:end])
        cursor = max(cursor, end)

    if cursor < n:
        parts.append(normalized_text[cursor:n])
    return "".join(parts)


def build_revision_metadata(
    normalized_text: str,
    clauses: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    decision_by_rec_id: dict[int, str],
) -> list[dict[str, Any]]:
    """Per-clause audit entries: span, original excerpt, what was applied, contributing decisions."""
    n = len(normalized_text)
    sorted_clauses = clamp_clauses_for_document(clauses, n)
    meta: list[dict[str, Any]] = []
    for c in sorted_clauses:
        cid = str(c.get("clause_id") or "")
        start = int(c.get("start_char") or 0)
        end = int(c.get("end_char") or 0)
        start = max(0, min(start, n))
        end = max(start, min(end, n))
        original = normalized_text[start:end]
        rewrite = _accepted_rewrite_for_clause(cid, recommendations, decision_by_rec_id) if cid else None
        applied = rewrite if rewrite is not None else original
        recs_here = [r for r in recommendations if (r.get("clause_id") or "") == cid]
        decisions_summary = [
            {
                "recommendation_id": int(r["id"]),
                "decision": decision_by_rec_id.get(int(r["id"]), DECISION_PENDING),
            }
            for r in recs_here
            if r.get("id") is not None
        ]
        changed = rewrite is not None and rewrite.strip() != original.strip()
        meta.append(
            {
                "clause_id": cid or None,
                "start_char": start,
                "end_char": end,
                "original_excerpt": original,
                "applied_text": applied,
                "changed": changed,
                "decisions": decisions_summary,
            }
        )
    return meta


def decision_map_from_rows(rows: list[tuple[int, str]]) -> dict[int, str]:
    """Build decision_by_rec_id from (recommendation_id, decision) pairs."""
    return {int(rid): str(d) for rid, d in rows}


def clamp_clauses_for_document(clauses: list[dict[str, Any]], text_len: int) -> list[dict[str, Any]]:
    """Sort by start and trim overlaps so each char is owned by at most one clause (later clause wins tail)."""
    sorted_clauses = sorted(
        clauses,
        key=lambda c: (int(c.get("start_char") or 0), int(c.get("end_char") or 0)),
    )
    out: list[dict[str, Any]] = []
    prev_end = 0
    for c in sorted_clauses:
        s = max(0, min(int(c.get("start_char") or 0), text_len))
        e = max(s, min(int(c.get("end_char") or 0), text_len))
        if s < prev_end:
            s = prev_end
        if e <= s:
            continue
        merged = dict(c)
        merged["start_char"] = s
        merged["end_char"] = e
        out.append(merged)
        prev_end = e
    return out
