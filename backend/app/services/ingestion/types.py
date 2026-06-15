"""
Typed schemas for the Extractor Agent (Agent 1).

RawExtractionResult: output of a provider (raw text, structure, warnings).
NormalizedExtraction: after normalization (encoding, whitespace).
ExtractionArtifact: full artifact for pipeline/API (includes document_metadata).
DocumentMetadata: filename, mime_type, size, page_count.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata about the source document (filename, type, size, optional page count)."""

    filename: str
    mime_type: str
    size_bytes: int = 0
    page_count: int | None = None


class RawExtractionResult(BaseModel):
    """
    Result of raw extraction from a single provider (PDF, DOCX, TXT, HTML).
    Structure and page_metadata are optional; warnings and error are for edge cases.
    """

    raw_text: str = ""
    structure: dict[str, Any] | None = None
    page_metadata: list[dict[str, Any]] | None = None
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class NormalizedExtraction(BaseModel):
    """
    Result after normalizing raw extraction: UTF-8, consistent whitespace.
    Warnings from raw extraction are carried over.
    """

    normalized_text: str = ""
    normalized_structure: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)


class ExtractionArtifact(BaseModel):
    """
    Full extraction artifact for the pipeline and API.
    Used by LangGraph state and GET /documents/{id}/extraction.
    """

    document_metadata: DocumentMetadata
    raw_text: str = ""
    normalized_text: str = ""
    structure: dict[str, Any] | None = None
    page_metadata: list[dict[str, Any]] | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
