"""Schemas for contract rewrite sessions and exports."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RecommendationIdBody(BaseModel):
    recommendation_id: int | None = None


class RewriteDecisionItemSchema(BaseModel):
    recommendation_id: int
    clause_id: str | None
    decision: str
    rewritten_clause: str | None
    issue_description: str | None
    severity: str | None
    priority: int | None
    framework: str | None
    article: str | None
    legal_rationale: str | None
    original_clause_text: str | None = None
    compliance_flags: list[str] = Field(default_factory=list)


class RewriteSessionSummarySchema(BaseModel):
    id: int
    document_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RewritesListResponse(BaseModel):
    document_id: int
    session: RewriteSessionSummarySchema
    items: list[RewriteDecisionItemSchema]


class RewriteGenerateResponse(BaseModel):
    document_id: int
    session_id: int
    status: str
    final_text_length: int
    changed_clauses: int
    message: str


class RewriteFinalResponse(BaseModel):
    document_id: int
    session_id: int
    final_text: str
    revision_metadata: list[dict[str, Any]]
    exports: list[dict[str, Any]]


class RewriteExportRecordSchema(BaseModel):
    id: int
    kind: str
    file_path: str
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}
