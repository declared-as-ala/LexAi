"""
NLP Analyzer Agent (Agent 2): language detection, clause segmentation,
entity extraction, and clause classification.
"""

from app.services.nlp.taxonomy import ClauseLabel, ComplianceFlag, EntityLabel, TAXONOMY
from app.services.nlp.language_detector import LanguageDetector
from app.services.nlp.clause_segmenter import ClauseSegmenter
from app.services.nlp.entity_extractor import EntityExtractor
from app.services.nlp.clause_classifier import ClauseClassifier

__all__ = [
    "ClauseLabel",
    "ComplianceFlag",
    "EntityLabel",
    "TAXONOMY",
    "LanguageDetector",
    "ClauseSegmenter",
    "EntityExtractor",
    "ClauseClassifier",
]
