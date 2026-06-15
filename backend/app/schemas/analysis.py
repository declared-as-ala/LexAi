"""Pydantic schemas for Agent 2 NLP Analysis API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EntitySchema(BaseModel):
    text: str
    label: str
    start: int
    end: int
    confidence: float
    source: str


class ClauseAnalysisSchema(BaseModel):
    clause_id: str
    text: str
    start_char: int
    end_char: int
    section_title: str | None
    source: str
    labels: list[str]
    compliance_flags: list[str]
    entities: list[EntitySchema]
    confidence: float
    model_used: str


class NLPAnalysisResponse(BaseModel):
    document_id: int
    analysis_id: int
    language: str | None
    language_confidence: float | None
    clause_count: int
    risk_level: str | None
    compliance_score: float | None
    model_used: str | None
    created_at: datetime
    clauses: list[ClauseAnalysisSchema]

    model_config = {"from_attributes": True}


class NLPAnalysisSummaryResponse(BaseModel):
    document_id: int
    analysis_id: int
    language: str | None
    language_confidence: float | None
    clause_count: int
    risk_level: str | None
    compliance_score: float | None
    model_used: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClauseDetailResponse(BaseModel):
    document_id: int
    clause: ClauseAnalysisSchema


class ClauseListResponse(BaseModel):
    document_id: int
    total_count: int
    items: list[ClauseAnalysisSchema]
