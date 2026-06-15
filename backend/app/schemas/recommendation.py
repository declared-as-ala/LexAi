"""Pydantic schemas for Agent 4 Recommendation API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RecommendationItemSchema(BaseModel):
    id: int
    priority: int | None
    framework: str | None
    article: str | None
    severity: str | None
    clause_id: str | None
    violation_id: str | None
    violation_rule_id: str | None
    issue_description: str | None
    recommendation_text: str | None
    rewritten_clause: str | None
    legal_rationale: str | None
    generated_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationsListResponse(BaseModel):
    document_id: int
    total: int
    recommendations: list[RecommendationItemSchema]


class RecommendTriggerResponse(BaseModel):
    document_id: int
    task_id: str | None
    message: str
