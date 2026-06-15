"""Unit tests for ClauseClassifier (Agent 2) — heuristic path only (no model download needed)."""

import pytest
from app.services.nlp.clause_segmenter import ClauseSegment
from app.services.nlp.clause_classifier import ClauseClassifier
from app.services.nlp.taxonomy import ClauseLabel, ComplianceFlag


def make_clause(text: str, clause_id: str = "c-001") -> ClauseSegment:
    return ClauseSegment(
        clause_id=clause_id,
        text=text,
        start_char=0,
        end_char=len(text),
    )


# Force heuristic mode by patching away the pipeline
@pytest.fixture(autouse=True)
def no_pipeline(monkeypatch):
    monkeypatch.setattr(
        "app.services.nlp.clause_classifier.ClauseClassifier._load_pipeline",
        lambda self: None,
    )


def test_classifies_data_processing_clause():
    clause = make_clause(
        "Le prestataire s'engage à traiter les données personnelles des utilisateurs "
        "uniquement pour les finalités définies au présent contrat."
    )
    result = ClauseClassifier().classify(clause)
    assert ClauseLabel.DATA_PROCESSING.value in result.labels
    assert result.model_used == "heuristic"
    assert 0.0 < result.confidence <= 1.0


def test_classifies_confidentiality_clause():
    clause = make_clause(
        "Les parties s'engagent à garder confidentielles toutes les informations "
        "échangées dans le cadre de ce contrat et à ne pas les divulguer à des tiers."
    )
    result = ClauseClassifier().classify(clause)
    assert ClauseLabel.CONFIDENTIALITY.value in result.labels


def test_classifies_liability_clause():
    clause = make_clause(
        "La responsabilité du prestataire est limitée au montant des honoraires perçus. "
        "En aucun cas le prestataire ne sera tenu pour les dommages indirects."
    )
    result = ClauseClassifier().classify(clause)
    assert ClauseLabel.LIABILITY.value in result.labels


def test_classifies_termination_clause():
    clause = make_clause(
        "Chaque partie peut mettre fin au contrat et procéder à sa résiliation "
        "avec un préavis de 30 jours par lettre recommandée."
    )
    result = ClauseClassifier().classify(clause)
    assert ClauseLabel.TERMINATION.value in result.labels


def test_classifies_penalty_clause():
    clause = make_clause(
        "En cas de manquement, des pénalités de retard seront appliquées ainsi que "
        "des dommages-intérêts calculés selon les termes convenus."
    )
    result = ClauseClassifier().classify(clause)
    assert ClauseLabel.PENALTY.value in result.labels


def test_flags_lnpdp_relevant():
    clause = make_clause(
        "Le traitement des données est régi par la LNPDP loi n°2004-63 "
        "portant sur la protection des données à caractère personnel en Tunisie."
    )
    result = ClauseClassifier().classify(clause)
    assert ComplianceFlag.LNPDP_RELEVANT.value in result.compliance_flags


def test_flags_gdpr_relevant():
    clause = make_clause(
        "Conformément au RGPD, le responsable du traitement s'engage à respecter "
        "les principes du règlement général sur la protection des données."
    )
    result = ClauseClassifier().classify(clause)
    assert ComplianceFlag.GDPR_RELEVANT.value in result.compliance_flags


def test_flags_missing_retention_period():
    clause = make_clause(
        "Le prestataire traite les données personnelles des clients "
        "pour les besoins de l'exécution du contrat de service."
    )
    result = ClauseClassifier().classify(clause)
    assert ComplianceFlag.MISSING_RETENTION_PERIOD.value in result.compliance_flags


def test_no_missing_retention_when_duration_specified():
    clause = make_clause(
        "Les données personnelles sont conservées pendant une durée de conservation "
        "de 5 ans puis supprimées. La période de conservation est strictement limitée."
    )
    result = ClauseClassifier().classify(clause)
    assert ComplianceFlag.MISSING_RETENTION_PERIOD.value not in result.compliance_flags


def test_classify_all_returns_dict():
    clauses = [
        make_clause("Le contrat porte sur la prestation de services.", "c-001"),
        make_clause("Les données personnelles sont traitées conformément à la LNPDP.", "c-002"),
        make_clause("La responsabilité est limitée aux dommages directs.", "c-003"),
    ]
    results = ClauseClassifier().classify_all(clauses)
    assert set(results.keys()) == {"c-001", "c-002", "c-003"}
    for r in results.values():
        assert isinstance(r.labels, list)
        assert isinstance(r.compliance_flags, list)


def test_empty_clause_returns_result():
    clause = make_clause("")
    result = ClauseClassifier().classify(clause)
    assert isinstance(result.labels, list)
    assert isinstance(result.compliance_flags, list)


def test_labels_are_valid_taxonomy_values():
    clause = make_clause(
        "Le prestataire s'engage à maintenir la confidentialité des informations "
        "et à ne pas divulguer les données personnelles à des tiers."
    )
    result = ClauseClassifier().classify(clause)
    valid_labels = {l.value for l in ClauseLabel}
    valid_flags = {f.value for f in ComplianceFlag}
    for label in result.labels:
        assert label in valid_labels, f"Unknown label: {label}"
    for flag in result.compliance_flags:
        assert flag in valid_flags, f"Unknown flag: {flag}"
