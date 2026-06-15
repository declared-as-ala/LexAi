"""Agent 3 — LangGraph node: legal evaluation."""

from __future__ import annotations

from app.core.logging import get_logger
from app.workflows.state import AnalysisState

logger = get_logger(__name__)


def evaluate_document(state: AnalysisState) -> AnalysisState:
    """LangGraph node: run legal evaluation using Agent 3 rule engine."""
    from app.legal.rule_engine import evaluate
    from app.legal.scorer import compute_scores

    document_id = state.get("document_id")
    clauses: list[dict] = state.get("clauses", [])

    if not clauses:
        logger.warning("evaluate_node_no_clauses", extra={"extra": {"document_id": document_id}})
        return {**state, "scores": {}, "findings": [], "errors": [*(state.get("errors") or []), "No clauses to evaluate"]}

    try:
        eval_result = evaluate(clauses)
        score_result = compute_scores(eval_result.violations, eval_result.active_frameworks)

        findings = [
            {
                "violation_id": v.violation_id,
                "rule_id": v.rule_id,
                "framework": v.framework,
                "article": v.article,
                "title": v.title,
                "description": v.description,
                "severity": v.severity,
                "clause_id": v.clause_id,
                "clause_text": v.clause_text,
                "remediation_hint": v.remediation_hint,
            }
            for v in eval_result.violations
        ]

        scores = {
            "global_score": score_result.global_score,
            "litigation_risk": score_result.litigation_risk,
            "framework_scores": score_result.framework_scores,
            "active_frameworks": eval_result.active_frameworks,
            "missing_clauses": eval_result.missing_clause_keys,
        }

        logger.info(
            "evaluate_node_complete",
            extra={"extra": {
                "document_id": document_id,
                "violations": len(findings),
                "global_score": score_result.global_score,
            }},
        )

        return {**state, "findings": findings, "scores": scores}

    except Exception as exc:
        logger.exception("evaluate_node_error", extra={"extra": {"document_id": document_id, "error": str(exc)}})
        return {**state, "errors": [*(state.get("errors") or []), str(exc)]}
