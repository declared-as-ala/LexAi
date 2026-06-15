"""API response schemas for documents and extractions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UploadDocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    progress_percent: int
    progress_stage: str
    progress_message: str | None = None


class DocumentBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    filename: str
    mime_type: str
    size_bytes: int
    status: str
    progress_percent: int
    progress_stage: str
    progress_message: str | None = None
    last_error: str | None = None
    task_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    finished_at: datetime | None = None


class DocumentDetailResponse(DocumentBaseResponse):
    pass


class DocumentListResponse(BaseModel):
    items: list[DocumentBaseResponse]
    total_count: int


class DocumentMetadataSchema(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int = 0
    page_count: int | None = None


class ExtractionPayload(BaseModel):
    document_metadata: DocumentMetadataSchema
    raw_text: str = ""
    normalized_text: str = ""
    structure: dict[str, Any] | None = None
    page_metadata: list[dict[str, Any]] | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    document_id: int
    extraction: ExtractionPayload | None = None
    message: str | None = None


class DocumentSummaryResponse(BaseModel):
    queued_count: int
    extracting_count: int
    extracted_count: int
    analyzing_count: int = 0
    analyzed_count: int = 0
    evaluating_count: int = 0
    evaluated_count: int = 0
    recommending_count: int = 0
    complete_count: int = 0
    failed_count: int
    total_count: int
    agent1_success_rate: float = 0.0
    agent2_success_rate: float = 0.0
    agent3_success_rate: float = 0.0
    agent4_success_rate: float = 0.0


class RetryDocumentResponse(BaseModel):
    id: int
    status: str
    progress_percent: int
    progress_stage: str
    progress_message: str | None = None