"""Unit tests for ClauseSegmenter (Agent 2)."""

import pytest
from app.services.nlp.clause_segmenter import ClauseSegmenter


SAMPLE_CONTRACT = """Article 1 — Objet du contrat
Le présent contrat a pour objet la fourniture de services informatiques.

Article 2 — Durée
Le contrat est conclu pour une durée de 12 mois à compter de la date de signature.

Article 3 — Protection des données
Le prestataire s'engage à traiter les données personnelles des utilisateurs
conformément à la loi n°2004-63 portant sur la protection des données à caractère personnel.

Article 4 — Résiliation
Chaque partie peut mettre fin au contrat avec un préavis de 30 jours."""


def test_segments_articles_by_regex():
    segs = ClauseSegmenter().segment(SAMPLE_CONTRACT)
    assert len(segs) >= 4


def test_clause_ids_are_sequential():
    segs = ClauseSegmenter().segment(SAMPLE_CONTRACT)
    ids = [s.clause_id for s in segs]
    assert ids == [f"c-{i:03d}" for i in range(1, len(segs) + 1)]


def test_clause_text_is_not_empty():
    segs = ClauseSegmenter().segment(SAMPLE_CONTRACT)
    for seg in segs:
        assert seg.text.strip() != ""


def test_clause_char_offsets_match_text():
    segs = ClauseSegmenter().segment(SAMPLE_CONTRACT)
    for seg in segs:
        extracted = SAMPLE_CONTRACT[seg.start_char:seg.end_char]
        assert seg.text in extracted or extracted in seg.text


def test_empty_text_returns_empty_list():
    segs = ClauseSegmenter().segment("")
    assert segs == []


def test_whitespace_only_returns_empty_list():
    segs = ClauseSegmenter().segment("   \n\n  ")
    assert segs == []


def test_segments_by_structure_json():
    text = "Intro text here.\n\nSection on data.\n\nSection on liability."
    structure = {
        "sections": [
            {"title": "Introduction", "level": 1, "start_char": 0},
            {"title": "Data", "level": 1, "start_char": 18},
            {"title": "Liability", "level": 1, "start_char": 37},
        ]
    }
    segs = ClauseSegmenter().segment(text, structure_json=structure)
    assert len(segs) >= 2
    assert segs[0].source == "structure"


def test_paragraph_fallback_for_plain_text():
    text = "First paragraph about obligations of the party.\n\nSecond paragraph about payment terms and invoicing dates.\n\nThird paragraph about confidentiality and non-disclosure."
    segs = ClauseSegmenter().segment(text)
    assert len(segs) == 3
    assert all(s.source == "paragraph" for s in segs)


def test_section_title_set_when_regex_matches():
    segs = ClauseSegmenter().segment(SAMPLE_CONTRACT)
    # At least some segments should have a section_title from regex
    titled = [s for s in segs if s.section_title]
    assert len(titled) > 0
