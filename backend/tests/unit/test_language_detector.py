"""Unit tests for LanguageDetector (Agent 2)."""

from app.services.nlp.language_detector import LanguageDetector


def test_detects_french_by_heuristic():
    text = "Le présent contrat est conclu entre les parties suivantes pour une durée de 12 mois."
    result = LanguageDetector().detect(text)
    assert result.language == "fr"
    assert result.confidence > 0


def test_detects_arabic_by_char_range():
    text = "هذا العقد مبرم بين الطرفين التاليين وفقاً للقانون التونسي"
    result = LanguageDetector().detect(text)
    assert result.language == "ar"
    assert result.method == "arabic_chars"


def test_returns_unknown_for_empty_text():
    result = LanguageDetector().detect("")
    assert result.language == "unknown"
    assert result.confidence == 0.0


def test_returns_unknown_for_whitespace():
    result = LanguageDetector().detect("   \n\n  ")
    assert result.language == "unknown"


def test_detects_french_contract_text():
    text = """
    Article 1 — Objet du contrat
    Le prestataire s'engage à fournir des services informatiques au client.
    Les données personnelles traitées dans le cadre de ce contrat sont protégées
    conformément à la loi n°2004-63 portant sur la protection des données à caractère personnel.
    """
    result = LanguageDetector().detect(text)
    assert result.language == "fr"
