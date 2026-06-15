"""Agent 4 — Recommendation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import STATUS_COMPLETE, STATUS_EVALUATED
from app.db.models.document import Document
from app.db.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationItemSchema, RecommendationsListResponse, RecommendTriggerResponse

router = APIRouter(prefix="/documents", tags=["recommendations"])


def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})
    return doc


@router.get("/{document_id}/recommendations", response_model=RecommendationsListResponse)
def list_recommendations(document_id: int, db: Session = Depends(get_db)) -> RecommendationsListResponse:
    """List all persisted recommendations for a document."""
    _get_document_or_404(document_id, db)
    rows = (
        db.query(Recommendation)
        .filter(Recommendation.document_id == document_id)
        .order_by(Recommendation.priority.asc(), Recommendation.id.asc())
        .all()
    )
    return RecommendationsListResponse(
        document_id=document_id,
        total=len(rows),
        recommendations=[RecommendationItemSchema.model_validate(r) for r in rows],
    )


@router.post("/{document_id}/recommend", response_model=RecommendTriggerResponse, status_code=202)
def trigger_recommendations(document_id: int, db: Session = Depends(get_db)) -> RecommendTriggerResponse:
    """Manually trigger (or re-trigger) recommendation generation."""
    from app.tasks.recommendation import enqueue_recommendation

    doc = _get_document_or_404(document_id, db)
    if doc.status not in {STATUS_EVALUATED, STATUS_COMPLETE}:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "invalid_state",
                "message": f"Cannot generate recommendations in status '{doc.status}'. "
                "Document must be 'evaluated' or 'complete'.",
            },
        )
    task_id = enqueue_recommendation(document_id)
    return RecommendTriggerResponse(
        document_id=document_id,
        task_id=task_id,
        message="Recommendations queued.",
    )
