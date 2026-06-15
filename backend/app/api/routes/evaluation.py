"""Agent 3 — Legal Evaluation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.document import Document
from app.db.models.evaluation import Evaluation
from app.schemas.evaluation import (
    EvaluationResponse,
    EvaluationSummaryResponse,
    EvaluateTriggerResponse,
    ViolationSchema,
)

router = APIRouter(prefix="/documents", tags=["evaluation"])


def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})
    return doc


def _get_evaluation_or_404(document_id: int, db: Session) -> Evaluation:
    evaluation = (
        db.query(Evaluation)
        .filter(Evaluation.document_id == document_id)
        .first()
    )
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail={"code": "evaluation_not_found", "message": "No evaluation found. Run analysis first."},
        )
    return evaluation


def _build_response(evaluation: Evaluation) -> EvaluationResponse:
    violations = [ViolationSchema(**v) for v in evaluation.get_violations()]
    fw_scores: dict[str, float] = {}
    fw_counts: dict[str, int] = evaluation.get_violation_counts()
    for fw, col in [
        ("LNPDP", evaluation.lnpdp_score),
        ("GDPR", evaluation.gdpr_score),
        ("ISO27001", evaluation.iso27001_score),
        ("ISO9001", evaluation.iso9001_score),
    ]:
        if col is not None:
            fw_scores[fw] = col

    return EvaluationResponse(
        document_id=evaluation.document_id,
        evaluation_id=evaluation.id,
        global_score=evaluation.global_score,
        litigation_risk=evaluation.litigation_risk,
        framework_scores=fw_scores,
        framework_violation_counts=fw_counts,
        active_frameworks=evaluation.get_active_frameworks(),
        violations=violations,
        missing_clauses=evaluation.get_missing_clauses(),
        violation_count=len(violations),
        evaluated_at=evaluation.evaluated_at,
        created_at=evaluation.created_at,
    )


@router.get("/{document_id}/evaluation", response_model=EvaluationResponse)
def get_evaluation(document_id: int, db: Session = Depends(get_db)) -> EvaluationResponse:
    """Get the full legal evaluation result for a document."""
    _get_document_or_404(document_id, db)
    evaluation = _get_evaluation_or_404(document_id, db)
    return _build_response(evaluation)


@router.get("/{document_id}/evaluation/summary", response_model=EvaluationSummaryResponse)
def get_evaluation_summary(document_id: int, db: Session = Depends(get_db)) -> EvaluationSummaryResponse:
    """Get evaluation summary (scores only, no violation details)."""
    _get_document_or_404(document_id, db)
    evaluation = _get_evaluation_or_404(document_id, db)
    fw_scores: dict[str, float] = {}
    for fw, col in [
        ("LNPDP", evaluation.lnpdp_score),
        ("GDPR", evaluation.gdpr_score),
        ("ISO27001", evaluation.iso27001_score),
        ("ISO9001", evaluation.iso9001_score),
    ]:
        if col is not None:
            fw_scores[fw] = col

    return EvaluationSummaryResponse(
        document_id=document_id,
        evaluation_id=evaluation.id,
        global_score=evaluation.global_score,
        litigation_risk=evaluation.litigation_risk,
        framework_scores=fw_scores,
        active_frameworks=evaluation.get_active_frameworks(),
        violation_count=len(evaluation.get_violations()),
        missing_clause_count=len(evaluation.get_missing_clauses()),
        evaluated_at=evaluation.evaluated_at,
        created_at=evaluation.created_at,
    )


@router.post("/{document_id}/evaluate", response_model=EvaluateTriggerResponse, status_code=202)
def trigger_evaluation(document_id: int, db: Session = Depends(get_db)) -> EvaluateTriggerResponse:
    """Manually trigger (or re-trigger) legal evaluation for a document."""
    from app.core.config import STATUS_ANALYZED, STATUS_COMPLETE, STATUS_EVALUATED
    from app.tasks.evaluation import enqueue_evaluation

    doc = _get_document_or_404(document_id, db)
    if doc.status not in {STATUS_ANALYZED, STATUS_EVALUATED, STATUS_COMPLETE}:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "invalid_state",
                "message": f"Cannot evaluate document in status '{doc.status}'. Must be 'analyzed', 'evaluated', or 'complete'.",
            },
        )
    task_id = enqueue_evaluation(document_id)
    return EvaluateTriggerResponse(
        document_id=document_id,
        task_id=task_id,
        message="Legal evaluation queued.",
    )
