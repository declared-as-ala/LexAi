"""Tests for hybrid Agent 4 LLM enhancement (mocked, no real API calls)."""

from __future__ import annotations

import json
from unittest.mock import patch

from app.services.llm.llm_service import enhance_recommendation_rows
from app.services.llm.refine_recommendations import refine_recommendation_rows


def _sample_row(vid: str = "v-1", cid: str = "c-001") -> dict:
    return {
        "violation_id": vid,
        "clause_id": cid,
        "violation_rule_id": "RULE_X",
        "framework": "GDPR",
        "article": "Art. 6",
        "severity": "high",
        "priority": 1,
        "issue_description": "Issue original",
        "recommendation_text": "Reco original",
        "rewritten_clause": "Clause rewrite original",
        "legal_rationale": "Rationale original",
        "generated_by": "template_v1",
    }


def _violations() -> list[dict]:
    return [
        {
            "violation_id": "v-1",
            "rule_id": "RULE_X",
            "framework": "GDPR",
            "article": "Art. 6",
            "title": "Titre",
            "description": "Desc",
            "severity": "high",
            "clause_id": "c-001",
            "clause_text": "Texte clause",
            "remediation_hint": "Hint",
        }
    ]


def _clauses() -> list[dict]:
    return [{"clause_id": "c-001", "text": "Clause NLP complète."}]


def test_refine_skipped_when_llm_disabled():
    with patch("app.services.llm.llm_service.LLM_ENABLED", False):
        rows = [_sample_row()]
        out = refine_recommendation_rows(rows, [], _clauses())
        assert out == rows
        assert out[0]["generated_by"] == "template_v1"


def test_enhance_applies_llm_when_valid_json():
    llm_payload = {
        "improved_rewrite": "Clause améliorée",
        "clear_explanation": "Explication claire",
        "risk_summary": "Synthèse risque",
    }
    with patch("app.services.llm.llm_service.LLM_ENABLED", True):
        with patch(
            "app.services.llm.llm_service.groq_chat_completion_content",
            return_value=json.dumps(llm_payload),
        ):
            rows = [_sample_row()]
            out = enhance_recommendation_rows(rows, _violations(), _clauses())
    assert len(out) == 1
    assert out[0]["generated_by"] == "llm_v2"
    assert out[0]["issue_description"] == "Synthèse risque"
    assert out[0]["recommendation_text"] == "Explication claire"
    assert out[0]["rewritten_clause"] == "Clause améliorée"
    assert out[0]["legal_rationale"] == "Rationale original"


def test_enhance_fallback_on_bad_json():
    with patch("app.services.llm.llm_service.LLM_ENABLED", True):
        with patch(
            "app.services.llm.llm_service.groq_chat_completion_content",
            return_value="not json",
        ):
            rows = [_sample_row()]
            out = enhance_recommendation_rows(rows, _violations(), _clauses())
    assert out[0]["generated_by"] == "template_v1"


def test_merge_same_clause_returns_single_row():
    llm_payload = {
        "improved_rewrite": "Clause fusionnée",
        "clear_explanation": "Mesures combinées",
        "risk_summary": "Risque global",
    }
    rows = [
        {**_sample_row("v-1", "c-001"), "priority": 1, "severity": "high"},
        {**_sample_row("v-2", "c-001"), "priority": 2, "severity": "medium", "violation_rule_id": "RULE_Y"},
    ]
    viols = [
        _violations()[0],
        {
            **{k: v for k, v in _violations()[0].items() if k != "violation_id"},
            "violation_id": "v-2",
        },
    ]
    with patch("app.services.llm.llm_service.LLM_ENABLED", True):
        with patch(
            "app.services.llm.llm_service.groq_chat_completion_content",
            return_value=json.dumps(llm_payload),
        ):
            out = enhance_recommendation_rows(rows, viols, _clauses())
    assert len(out) == 1
    assert out[0]["generated_by"] == "llm_v2"
    assert out[0]["rewritten_clause"] == "Clause fusionnée"
    assert "v-1" in (out[0].get("legal_rationale") or "")
    assert "v-2" in (out[0].get("legal_rationale") or "")


def test_null_clause_ids_not_merged():
    llm_payload = {
        "improved_rewrite": "X",
        "clear_explanation": "Y",
        "risk_summary": "Z",
    }
    rows = [
        {**_sample_row("v-1", "c-001"), "clause_id": None},
        {**_sample_row("v-2", "c-002"), "clause_id": None},
    ]
    with patch("app.services.llm.llm_service.LLM_ENABLED", True):
        with patch(
            "app.services.llm.llm_service.groq_chat_completion_content",
            return_value=json.dumps(llm_payload),
        ):
            out = enhance_recommendation_rows(rows, [], [])
    assert len(out) == 2
