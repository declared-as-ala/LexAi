"""
Typed state for the analysis LangGraph.
Holds document_id, extraction_result, normalized_text, clauses, findings, scores, recommendations, errors.
Uses TypedDict for LangGraph compatibility (state merge).
"""

from typing import Any, TypedDict


class AnalysisState(TypedDict, total=False):
    """Shared state across workflow nodes (LangGraph merge-friendly)."""

    request_id: str | None
    user_id: int | None
    document_id: int | None
    file_metadata: dict[str, Any]
    extraction_result: dict[str, Any] | None
    normalized_text: str
    clauses: list[dict[str, Any]]
    entities: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    scores: dict[str, Any]
    recommendations: list[dict[str, Any]]
    errors: list[str]
    audit_trace: list[dict[str, Any]]
