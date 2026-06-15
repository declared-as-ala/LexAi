"""Unit tests for EntityExtractor (Agent 2)."""

import pytest
from app.services.nlp.clause_segmenter import ClauseSegment
from app.services.nlp.entity_extractor import EntityExtractor
from app.services.nlp.taxonomy import EntityLabel


def make_clause(text: str, clause_id: str = "c-001") -> ClauseSegment:
    return ClauseSegment(
        clause_id=clause_id,
        text=text,
        start_char=0,
        end_char=len(text),
    )


def test_detects_law_reference_lnpdp():
    clause = make_clause("Le traitement est soumis à la LNPDP et ses dispositions.")
    entities = EntityExtractor().extract(clause)
    labels = [e.label for e in entities]
    assert EntityLabel.LAW_REFERENCE.value in labels


def test_detects_law_reference_rgpd():
    clause = make_clause("Ce contrat est conforme au RGPD et au règlement général sur la protection des données.")
    entities = EntityExtractor().extract(clause)
    labels = [e.label for e in entities]
    assert EntityLabel.LAW_REFERENCE.value in labels


def test_detects_data_category():
    clause = make_clause("Le prestataire traite les données personnelles des utilisateurs.")
    entities = EntityExtractor().extract(clause)
    labels = [e.label for e in entities]
    assert EntityLabel.DATA_CATEGORY.value in labels


def test_detects_role_responsable():
    clause = make_clause("Le responsable du traitement s'engage à respecter les obligations légales.")
    entities = EntityExtractor().extract(clause)
    labels = [e.label for e in entities]
    assert EntityLabel.ROLE.value in labels


def test_detects_duration():
    clause = make_clause("Les données sont conservées pendant 5 ans après la fin du contrat.")
    entities = EntityExtractor().extract(clause)
    labels = [e.label for e in entities]
    assert EntityLabel.DURATION.value in labels


def test_detects_jurisdiction_tunisie():
    clause = make_clause("Le présent contrat est régi par le droit tunisien et les lois de la Tunisie.")
    entities = EntityExtractor().extract(clause)
    labels = [e.label for e in entities]
    assert EntityLabel.JURISDICTION.value in labels


def test_entity_spans_within_text():
    text = "Le responsable du traitement conserve les données personnelles pendant 30 jours."
    clause = make_clause(text)
    entities = EntityExtractor().extract(clause)
    for e in entities:
        assert 0 <= e.start < e.end <= len(text)
        assert text[e.start:e.end].lower() in e.text.lower() or e.text.lower() in text[e.start:e.end].lower()


def test_empty_clause_returns_empty_list():
    clause = make_clause("")
    entities = EntityExtractor().extract(clause)
    assert entities == []


def test_extract_all_returns_dict_keyed_by_clause_id():
    clauses = [
        make_clause("Le prestataire traite les données personnelles.", "c-001"),
        make_clause("Durée de conservation: 12 mois.", "c-002"),
    ]
    result = EntityExtractor().extract_all(clauses)
    assert set(result.keys()) == {"c-001", "c-002"}
    assert isinstance(result["c-001"], list)
    assert isinstance(result["c-002"], list)


def test_no_duplicate_spans():
    text = "Le responsable du traitement traite les données personnelles selon la LNPDP."
    clause = make_clause(text)
    entities = EntityExtractor().extract(clause)
    spans = [(e.start, e.end) for e in entities]
    assert len(spans) == len(set(spans)), "Duplicate entity spans found"
