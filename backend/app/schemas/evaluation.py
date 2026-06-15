"""Pydantic schemas for Agent 3 Evaluation API responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ViolationSchema(BaseModel):
    violation_id: str
    rule_id: str
    framework: str
    article: str
    title: str
    description: str
    severity: str
    clause_id: str | None
    clause_text: str | None
    remediation_hint: str


class EvaluationResponse(BaseModel):
    document_id: int
    evaluation_id: int
    global_score: float | None
    litigation_risk: str | None
    framework_scores: dict[str, float]
    framework_violation_counts: dict[str, int]
    active_frameworks: list[str]
    violations: list[ViolationSchema]
    missing_clauses: list[str]
    violation_count: int
    evaluated_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationSummaryResponse(BaseModel):
    document_id: int
    evaluation_id: int
    global_score: float | None
    litigation_risk: str | None
    framework_scores: dict[str, float]
    active_frameworks: list[str]
    violation_count: int
    missing_clause_count: int
    evaluated_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluateTriggerResponse(BaseModel):
    document_id: int
    task_id: str | None
    message: str
