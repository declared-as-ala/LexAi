"""Agent 4 hybrid refinement — delegates to llm_service.enhance_recommendation_rows."""

from __future__ import annotations

from typing import Any

from app.services.llm.llm_service import enhance_recommendation_rows


def refine_recommendation_rows(
    rows: list[dict[str, Any]],
    violations: list[dict[str, Any]],
    clauses: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    template_result → enhance_recommendation_rows() → final_result.

    ``clauses`` should be Agent 2 clause dicts (for original_clause text). If omitted, empty list.
    """
    return enhance_recommendation_rows(rows, violations, clauses or [])
