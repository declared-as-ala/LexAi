"""
EntityExtractor — Agent 2 submodule.
Extracts named entities from clause text using:
  1. Fine-tuned spaCy model at data/models/ner_model/   (best accuracy, legal entities)
  2. Generic fr_core_news_lg                            (fallback if fine-tuned absent)
  3. Rule-based patterns                                (supplement for legal entities)

To train the fine-tuned model:
  python scripts/generate_synthetic.py
  python scripts/train_ner.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging import get_logger
from app.services.nlp.clause_segmenter import ClauseSegment
from app.services.nlp.taxonomy import EntityLabel

logger = get_logger(__name__)

# Path to fine-tuned spaCy NER model (produced by train_ner.py)
import os as _os
_DATA_DIR_NER = Path(_os.environ.get("DATA_DIR", Path(__file__).parent.parent.parent.parent.parent / "data"))
_FINETUNED_NER_DIR = _DATA_DIR_NER / "models" / "ner_model"


@dataclass
class Entity:
    text: str
    label: str          # EntityLabel value
    start: int          # char offset within clause text
    end: int
    confidence: float = 1.0
    source: str = "spacy"   # "spacy" | "rule"


# ------------------------------------------------------------------
# Rule-based pattern sets for legal entities not covered by spaCy
# ------------------------------------------------------------------

_ROLE_PATTERNS = [
    re.compile(r"\b(responsable\s+du\s+traitement|data\s+controller)\b", re.IGNORECASE),
    re.compile(r"\b(sous[\-\s]traitant|data\s+processor|prestataire)\b", re.IGNORECASE),
    re.compile(r"\b(délégué\s+à\s+la\s+protection\s+des\s+données|DPO|data\s+protection\s+officer)\b", re.IGNORECASE),
    re.compile(r"\b(personne\s+concernée|data\s+subject)\b", re.IGNORECASE),
    re.compile(r"\b(client|fournisseur|preneur|bailleur|employeur|employé|salarié)\b", re.IGNORECASE),
]

_DATA_CATEGORY_PATTERNS = [
    re.compile(r"\b(données?\s+à\s+caractère\s+personnel|données?\s+personnelles?)\b", re.IGNORECASE),
    re.compile(r"\b(données?\s+sensibles?|données?\s+de\s+santé|données?\s+biométriques?)\b", re.IGNORECASE),
    re.compile(r"\b(données?\s+financières?|données?\s+bancaires?)\b", re.IGNORECASE),
    re.compile(r"\b(informations?\s+confidentielles?|informations?\s+personnelles?)\b", re.IGNORECASE),
    re.compile(r"\b(personal\s+data|sensitive\s+data)\b", re.IGNORECASE),
]

_LAW_REFERENCE_PATTERNS = [
    re.compile(r"\b(LNPDP|loi\s+n°?\s*2004[\-\–]63|loi\s+organique\s+n°?\s*2004)\b", re.IGNORECASE),
    re.compile(r"\b(RGPD|GDPR|règlement\s+général|General\s+Data\s+Protection)\b", re.IGNORECASE),
    re.compile(r"\b(COC|code\s+des\s+obligations|code\s+civil)\b", re.IGNORECASE),
    re.compile(r"\b(Art\.?\s*\d+|article\s+\d+|§\s*\d+)\b", re.IGNORECASE),
    re.compile(r"\b(INPDP|autorité\s+de\s+protection)\b", re.IGNORECASE),
]

_DURATION_PATTERNS = [
    re.compile(r"\b\d+\s*(jours?|mois|ans?|années?|semaines?|heures?)\b", re.IGNORECASE),
    re.compile(r"\b(pendant\s+(la\s+durée|toute\s+la\s+durée)|durée\s+du\s+contrat)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*(days?|months?|years?|weeks?)\b", re.IGNORECASE),
]

_JURISDICTION_PATTERNS = [
    re.compile(r"\b(Tunisie|territoire\s+tunisien|droit\s+tunisien)\b", re.IGNORECASE),
    re.compile(r"\b(Union\s+européenne|territoire\s+de\s+l'Union|UE|EU)\b", re.IGNORECASE),
    re.compile(r"\b(France|Maroc|Algérie|droit\s+français|droit\s+marocain)\b", re.IGNORECASE),
    re.compile(r"\b(international|transfrontalier|cross[\-\s]border)\b", re.IGNORECASE),
]

_RULE_PATTERNS: list[tuple[list[re.Pattern], str]] = [
    (_ROLE_PATTERNS, EntityLabel.ROLE.value),
    (_DATA_CATEGORY_PATTERNS, EntityLabel.DATA_CATEGORY.value),
    (_LAW_REFERENCE_PATTERNS, EntityLabel.LAW_REFERENCE.value),
    (_DURATION_PATTERNS, EntityLabel.DURATION.value),
    (_JURISDICTION_PATTERNS, EntityLabel.JURISDICTION.value),
]

# spaCy label → our EntityLabel mapping
_SPACY_LABEL_MAP = {
    "PER": EntityLabel.PARTY.value,
    "PERSON": EntityLabel.PARTY.value,
    "ORG": EntityLabel.PARTY.value,
    "LOC": EntityLabel.JURISDICTION.value,
    "GPE": EntityLabel.JURISDICTION.value,
    "DATE": EntityLabel.DATE.value,
    "TIME": EntityLabel.DATE.value,
    "MONEY": EntityLabel.AMOUNT.value,
    "PERCENT": EntityLabel.AMOUNT.value,
    "CARDINAL": None,  # skip generic numbers
    "MISC": None,
}


class EntityExtractor:
    """Extract legal entities from clause segments."""

    def __init__(self, language: str = "fr"):
        self.language = language
        self._nlp = None   # lazy-loaded
        self._nlp_source = "none"

    def _load_nlp(self):
        if self._nlp is not None:
            return self._nlp
        try:
            import spacy  # type: ignore

            # 1. Try fine-tuned model
            if _FINETUNED_NER_DIR.exists() and (_FINETUNED_NER_DIR / "meta.json").exists():
                try:
                    self._nlp = spacy.load(str(_FINETUNED_NER_DIR))
                    self._nlp_source = "finetuned"
                    logger.info("ner_loaded_finetuned", extra={"extra": {"model": str(_FINETUNED_NER_DIR)}})
                    return self._nlp
                except Exception as exc:
                    logger.warning("finetuned_ner_load_failed", extra={"extra": {"error": str(exc)[:200]}})

            # 2. Generic French model
            generic = "fr_core_news_lg" if self.language == "fr" else "xx_ent_wiki_sm"
            try:
                self._nlp = spacy.load(generic)
                self._nlp_source = "generic"
                logger.info("ner_loaded_generic", extra={"extra": {"model": generic}})
            except OSError:
                logger.warning("spacy_model_not_found", extra={"extra": {"model": generic, "fallback": "rule_only"}})
                self._nlp = None
                self._nlp_source = "rule_only"
        except ImportError:
            logger.warning("spacy_not_installed", extra={"extra": {"fallback": "rule_only"}})
            self._nlp = None
            self._nlp_source = "rule_only"
        return self._nlp

    def extract(self, clause: ClauseSegment) -> list[Entity]:
        """Extract all entities from a single clause."""
        entities: list[Entity] = []
        text = clause.text

        # spaCy NER
        nlp = self._load_nlp()
        if nlp is not None:
            doc = nlp(text[:1000])  # cap at 1000 chars for performance
            for ent in doc.ents:
                mapped = _SPACY_LABEL_MAP.get(ent.label_)
                if mapped is None:
                    continue
                entities.append(Entity(
                    text=ent.text,
                    label=mapped,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.85,
                    source="spacy",
                ))

        # Rule-based patterns
        existing_spans = {(e.start, e.end) for e in entities}
        for patterns, label in _RULE_PATTERNS:
            for pattern in patterns:
                for m in pattern.finditer(text):
                    span = (m.start(), m.end())
                    if span in existing_spans:
                        continue
                    # Skip if fully contained within an existing span
                    if any(s <= m.start() and m.end() <= e for s, e in existing_spans):
                        continue
                    entities.append(Entity(
                        text=m.group(0),
                        label=label,
                        start=m.start(),
                        end=m.end(),
                        confidence=0.95,
                        source="rule",
                    ))
                    existing_spans.add(span)

        # Sort by position
        entities.sort(key=lambda e: e.start)
        return entities

    def extract_all(self, clauses: list[ClauseSegment]) -> dict[str, list[Entity]]:
        """Extract entities for all clauses. Returns {clause_id: [Entity]}."""
        return {clause.clause_id: self.extract(clause) for clause in clauses}
