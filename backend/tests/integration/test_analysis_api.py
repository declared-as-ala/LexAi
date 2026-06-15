"""Integration tests for Agent 2 NLP Analysis API endpoints."""

from __future__ import annotations

import pytest
from app.api.routes import documents as document_routes
from app.tasks.extraction import run_extraction_sync
from app.tasks.nlp_analysis import run_nlp_analysis_sync


# ── helpers ──────────────────────────────────────────────────────────────────

SAMPLE_CONTRACT = b"""Article 1 - Objet du contrat
Le prestataire s'engage a fournir des services informatiques au client.

Article 2 - Duree
Le contrat est conclu pour une duree de 12 mois a compter de la signature.

Article 3 - Protection des donnees
Le prestataire traite les donnees personnelles des utilisateurs conformement
a la loi n 2004-63 portant sur la protection des donnees a caractere personnel.
Le responsable du traitement s engage a respecter les droits des personnes.

Article 4 - Confidentialite
Les parties s engagent a garder confidentielles toutes les informations
echangees dans le cadre du present contrat.

Article 5 - Responsabilite
La responsabilite du prestataire est limitee au montant des honoraires."""


def _upload_and_extract(client, monkeypatch) -> int:
    """Upload a contract and run extraction synchronously. Returns document_id."""
    monkeypatch.setattr(
        document_routes, "enqueue_extraction",
        lambda doc_id: (run_extraction_sync(doc_id), None)[1],
    )
    response = client.post(
        "/documents/upload",
        files={"file": ("contract.txt", SAMPLE_CONTRACT, "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _upload_extract_and_analyze(client, monkeypatch) -> int:
    """Upload, extract, and run NLP analysis synchronously. Returns document_id."""
    doc_id = _upload_and_extract(client, monkeypatch)
    result = run_nlp_analysis_sync(doc_id)
    assert result["ok"], f"NLP analysis failed: {result}"
    return doc_id


# ── trigger endpoint ──────────────────────────────────────────────────────────

def test_trigger_analysis_on_extracted_document(client, monkeypatch):
    doc_id = _upload_and_extract(client, monkeypatch)

    # Patch enqueue to run sync
    monkeypatch.setattr(
        "app.api.routes.analysis.enqueue_nlp_analysis",
        lambda did: (run_nlp_analysis_sync(did), None)[1],
    )

    response = client.post(f"/documents/{doc_id}/analyze")
    assert response.status_code == 202
    data = response.json()
    assert data["document_id"] == doc_id
    assert "queued" in data["message"].lower() or "analysis" in data["message"].lower()


def test_trigger_analysis_rejects_queued_document(client, monkeypatch):
    monkeypatch.setattr(document_routes, "enqueue_extraction", lambda doc_id: None)
    response = client.post(
        "/documents/upload",
        files={"file": ("c.txt", b"hello", "text/plain")},
    )
    doc_id = response.json()["id"]

    response = client.post(f"/documents/{doc_id}/analyze")
    assert response.status_code == 409


def test_trigger_analysis_404_unknown_document(client):
    response = client.post("/documents/9999/analyze")
    assert response.status_code == 404


# ── analysis GET endpoints ────────────────────────────────────────────────────

def test_get_analysis_returns_clauses(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == doc_id
    assert data["clause_count"] > 0
    assert isinstance(data["clauses"], list)
    assert len(data["clauses"]) == data["clause_count"]


def test_get_analysis_clauses_have_required_fields(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/analysis")
    clauses = response.json()["clauses"]
    assert len(clauses) > 0

    for clause in clauses:
        assert "clause_id" in clause
        assert "text" in clause
        assert "labels" in clause
        assert "compliance_flags" in clause
        assert "entities" in clause
        assert isinstance(clause["labels"], list)
        assert isinstance(clause["compliance_flags"], list)
        assert isinstance(clause["entities"], list)


def test_get_analysis_detects_language(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/analysis")
    data = response.json()
    assert data["language"] in ("fr", "en", "unknown")


def test_get_analysis_summary_no_clauses_field(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/analysis/summary")
    assert response.status_code == 200
    data = response.json()
    assert "clause_count" in data
    assert "clauses" not in data


def test_get_analysis_404_before_analysis(client, monkeypatch):
    doc_id = _upload_and_extract(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/analysis")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "analysis_not_found"


def test_get_analysis_404_unknown_document(client):
    response = client.get("/documents/9999/analysis")
    assert response.status_code == 404


# ── clauses list endpoint ─────────────────────────────────────────────────────

def test_get_clauses_paginated(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/clauses?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "items" in data
    assert len(data["items"]) <= 2


def test_get_clauses_filter_by_label(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/clauses?label=data_processing")
    assert response.status_code == 200
    items = response.json()["items"]
    for clause in items:
        assert "data_processing" in clause["labels"]


def test_get_clauses_filter_by_compliance_flag(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/clauses?flag=lnpdp_relevant")
    assert response.status_code == 200
    items = response.json()["items"]
    for clause in items:
        assert "lnpdp_relevant" in clause["compliance_flags"]


def test_get_clauses_empty_filter_returns_empty(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/clauses?label=force_majeure")
    assert response.status_code == 200
    # May or may not have results — just ensure valid response
    assert "items" in response.json()


# ── clause detail endpoint ────────────────────────────────────────────────────

def test_get_clause_detail(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    # Get clause list then fetch first clause
    clauses_response = client.get(f"/documents/{doc_id}/clauses")
    clauses = clauses_response.json()["items"]
    assert len(clauses) > 0

    clause_id = clauses[0]["clause_id"]
    response = client.get(f"/documents/{doc_id}/clauses/{clause_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["clause"]["clause_id"] == clause_id
    assert data["document_id"] == doc_id


def test_get_clause_detail_404_unknown_id(client, monkeypatch):
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    response = client.get(f"/documents/{doc_id}/clauses/c-999")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "clause_not_found"


# ── full pipeline test ────────────────────────────────────────────────────────

def test_full_pipeline_agent1_then_agent2(client, monkeypatch):
    """End-to-end: upload → extract (Agent 1) → NLP analyze (Agent 2)."""
    doc_id = _upload_extract_and_analyze(client, monkeypatch)

    # Document should be in analyzed state
    doc_response = client.get(f"/documents/{doc_id}")
    assert doc_response.status_code == 200
    doc = doc_response.json()
    assert doc["status"] == "analyzed"
    assert doc["progress_percent"] == 100

    # Extraction should still be accessible
    extraction_response = client.get(f"/documents/{doc_id}/extraction")
    assert extraction_response.status_code == 200
    assert extraction_response.json()["extraction"]["normalized_text"] != ""

    # Analysis should be accessible
    analysis_response = client.get(f"/documents/{doc_id}/analysis")
    assert analysis_response.status_code == 200
    analysis = analysis_response.json()
    assert analysis["clause_count"] > 0
    assert analysis["language"] is not None

    # Summary count should reflect analyzed status
    summary = client.get("/documents/summary").json()
    assert summary["analyzed_count"] >= 1
