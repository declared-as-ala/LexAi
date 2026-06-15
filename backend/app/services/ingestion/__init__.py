"""
Extractor Agent (Agent 1): ingestion, raw extraction, normalization, storage.

Exposes: ExtractorService, get_provider, and types for use by API, Celery, and LangGraph.
"""

from app.services.ingestion.extractor_service import ExtractorService
from app.services.ingestion.types import (
    DocumentMetadata,
    ExtractionArtifact,
    NormalizedExtraction,
    RawExtractionResult,
)
from app.services.ingestion.providers import get_provider

__all__ = [
    "ExtractorService",
    "get_provider",
    "DocumentMetadata",
    "ExtractionArtifact",
    "NormalizedExtraction",
    "RawExtractionResult",
]
