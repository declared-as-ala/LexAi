"""Unit tests for deterministic rewrite assembly."""

from __future__ import annotations

from app.db.models.rewrite import DECISION_ACCEPTED, DECISION_PENDING, DECISION_REJECTED
from app.services.rewrite.engine import (
    build_revision_metadata,
    build_revised_text,
    clamp_clauses_for_document,
)


def test_build_revised_text_gap_and_tail():
    text = "AAA[BBB]CCC"
    clauses = [
        {"clause_id": "c-001", "start_char": 3, "end_char": 8, "text": "[BBB]"},
    ]
    recs = [{"id": 1, "clause_id": "c-001", "priority": 1, "rewritten_clause": "REWRITE"}]
    decisions = {1: DECISION_ACCEPTED}
    out = build_revised_text(text, clauses, recs, decisions)
    assert out == "AAAREWRITECCC"


def test_keep_original_when_not_accepted():
    text = "PREFIX[IN]SUFFIX"
    clauses = [{"clause_id": "c-001", "start_char": 6, "end_char": 9, "text": "IN"}]
    recs = [{"id": 10, "clause_id": "c-001", "priority": 1, "rewritten_clause": "OUT"}]
    decisions = {10: DECISION_REJECTED}
    out = build_revised_text(text, clauses, recs, decisions)
    assert out == "PREFIXINSUFFIX"


def test_multiple_clauses_order():
    text = "ab|cd|ef"
    clauses = [
        {"clause_id": "c-001", "start_char": 0, "end_char": 2, "text": "ab"},
        {"clause_id": "c-002", "start_char": 3, "end_char": 5, "text": "cd"},
        {"clause_id": "c-003", "start_char": 6, "end_char": 8, "text": "ef"},
    ]
    recs = [
        {"id": 1, "clause_id": "c-002", "priority": 0, "rewritten_clause": "XX"},
    ]
    decisions = {1: DECISION_ACCEPTED}
    out = build_revised_text(text, clauses, recs, decisions)
    assert out == "ab|XX|ef"


def test_priority_among_multiple_accepted_uses_lower_priority():
    text = "[[X]]"
    clauses = [{"clause_id": "c-001", "start_char": 0, "end_char": 5, "text": "[[X]]"}]
    recs = [
        {"id": 2, "clause_id": "c-001", "priority": 5, "rewritten_clause": "FIRST"},
        {"id": 3, "clause_id": "c-001", "priority": 1, "rewritten_clause": "SECOND"},
    ]
    decisions = {2: DECISION_ACCEPTED, 3: DECISION_ACCEPTED}
    out = build_revised_text(text, clauses, recs, decisions)
    assert out == "SECOND"


def test_empty_rewrite_falls_back_to_original():
    text = "ORIG"
    clauses = [{"clause_id": "c-001", "start_char": 0, "end_char": 4, "text": "ORIG"}]
    recs = [{"id": 1, "clause_id": "c-001", "priority": 0, "rewritten_clause": "   "}]
    decisions = {1: DECISION_ACCEPTED}
    out = build_revised_text(text, clauses, recs, decisions)
    assert out == "ORIG"


def test_clamp_overlapping_spans():
    text = "abcdefghij"
    raw = [
        {"clause_id": "c-001", "start_char": 0, "end_char": 6},
        {"clause_id": "c-002", "start_char": 3, "end_char": 10},
    ]
    fixed = clamp_clauses_for_document(raw, len(text))
    assert len(fixed) == 2
    assert fixed[0]["start_char"] == 0 and fixed[0]["end_char"] == 6
    assert fixed[1]["start_char"] == 6 and fixed[1]["end_char"] == 10


def test_revision_metadata_flags_changed():
    text = "HELLO"
    clauses = [{"clause_id": "c-001", "start_char": 0, "end_char": 5}]
    recs = [{"id": 1, "clause_id": "c-001", "priority": 0, "rewritten_clause": "HI"}]
    meta = build_revision_metadata(text, clauses, recs, {1: DECISION_ACCEPTED})
    assert len(meta) == 1
    assert meta[0]["changed"] is True
    assert meta[0]["applied_text"] == "HI"

    meta2 = build_revision_metadata(text, clauses, recs, {1: DECISION_PENDING})
    assert meta2[0]["changed"] is False
