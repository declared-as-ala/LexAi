"""
Registry: map MIME types (and optionally extensions) to DocumentExtractorProvider.
Unknown type raises ValueError (no silent fallback).
"""

from app.core.config import IMAGE_MIME_TYPES
from app.services.ingestion.providers.base import DocumentExtractorProvider
from app.services.ingestion.providers.docx import DocxProvider
from app.services.ingestion.providers.html import HtmlProvider
from app.services.ingestion.providers.ocr import OcrProvider
from app.services.ingestion.providers.pdf import PdfProvider
from app.services.ingestion.providers.txt import TxtProvider

_SUPPORTED_MIME_TYPES: dict[str, type[DocumentExtractorProvider]] = {
    "application/pdf": PdfProvider,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxProvider,
    "application/msword": DocxProvider,  # .doc; python-docx may open some
    "text/plain": TxtProvider,
    "text/html": HtmlProvider,
}
# All configured image types use Tesseract OCR
for _mime in sorted(IMAGE_MIME_TYPES):
    _SUPPORTED_MIME_TYPES[_mime] = OcrProvider

_provider_instances: dict[str, DocumentExtractorProvider] = {}


def get_provider(mime_type: str) -> DocumentExtractorProvider:
    """
    Return the extractor provider for the given MIME type.
    :param mime_type: e.g. application/pdf, text/plain.
    :return: DocumentExtractorProvider instance.
    :raises ValueError: if MIME type is not supported.
    """
    normalized = mime_type.strip().lower() if mime_type else ""
    if not normalized:
        raise ValueError("MIME type is required")
    if normalized not in _provider_instances:
        if normalized not in _SUPPORTED_MIME_TYPES:
            raise ValueError(
                f"Unsupported document type: {mime_type}. "
                f"Supported: {', '.join(sorted(_SUPPORTED_MIME_TYPES))}"
            )
        _provider_instances[normalized] = _SUPPORTED_MIME_TYPES[normalized]()
    return _provider_instances[normalized]
