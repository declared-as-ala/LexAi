"""
Provider registry: map MIME type to DocumentExtractorProvider.
get_provider(mime_type) returns the provider or raises ValueError for unknown types.
"""

from app.services.ingestion.providers.base import DocumentExtractorProvider
from app.services.ingestion.providers.registry import get_provider

__all__ = ["get_provider", "DocumentExtractorProvider"]
