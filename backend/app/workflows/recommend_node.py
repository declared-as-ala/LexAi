"""Agent 4 — LangGraph node: recommendations from evaluation + NLP."""

from __future__ import annotations

from app.core.logging import get_logger
from app.tasks.recommendation import run_recommendation_sync
from app.workflows.state import AnalysisState

logger = get_logger(__name__)


def recommend_clauses(state: AnalysisState) -> AnalysisState:
    """Persist Agent 4 recommendations (requires evaluation + NLP in DB)."""
    document_id = state.get("document_id")
    errors = list(state.get("errors") or [])
    audit_trace = list(state.get("audit_trace") or [])

    if document_id is None:
        errors.append("recommend_clauses: document_id is required")
        return {"errors": errors, "audit_trace": audit_trace}

    result = run_recommendation_sync(int(document_id))
    if not result.get("ok"):
        err = str(result.get("error") or "recommendation failed")
        errors.append(err)
        logger.warning("recommend_node_failed", extra={"extra": {"document_id": document_id, "error": err}})
        return {"errors": errors, "audit_trace": audit_trace}

    audit_trace.append({"node": "recommend_clauses", "status": "ok", "count": result.get("recommendation_count")})
    return {"recommendations": [], "errors": errors, "audit_trace": audit_trace}
