"""Agent 2 NLP Analysis API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models.document import Document
from app.db.models.nlp_analysis import NLPAnalysis
from app.schemas.analysis import (
    ClauseAnalysisSchema,
    ClauseDetailResponse,
    ClauseListResponse,
    NLPAnalysisResponse,
    NLPAnalysisSummaryResponse,
)

router = APIRouter(prefix="/documents", tags=["analysis"])


def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})
    return doc


def _get_analysis_or_404(document_id: int, db: Session) -> NLPAnalysis:
    analysis = (
        db.query(NLPAnalysis)
        .filter(NLPAnalysis.document_id == document_id)
        .order_by(NLPAnalysis.id.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail={"code": "analysis_not_found", "message": "No NLP analysis found. Run extraction first."},
        )
    return analysis


def _build_clause_schema(c: dict) -> ClauseAnalysisSchema:
    from app.schemas.analysis import EntitySchema
    return ClauseAnalysisSchema(
        clause_id=c["clause_id"],
        text=c["text"],
        start_char=c["start_char"],
        end_char=c["end_char"],
        section_title=c.get("section_title"),
        source=c.get("source", "paragraph"),
        labels=c.get("labels", []),
        compliance_flags=c.get("compliance_flags", []),
        entities=[EntitySchema(**e) for e in c.get("entities", [])],
        confidence=c.get("confidence", 0.0),
        model_used=c.get("model_used", "none"),
    )


@router.get("/{document_id}/analysis", response_model=NLPAnalysisResponse)
def get_document_analysis(document_id: int, db: Session = Depends(get_db)) -> NLPAnalysisResponse:
    """Get the full NLP analysis result for a document including all clauses."""
    _get_document_or_404(document_id, db)
    analysis = _get_analysis_or_404(document_id, db)
    clauses = [_build_clause_schema(c) for c in analysis.get_clauses()]
    return NLPAnalysisResponse(
        document_id=document_id,
        analysis_id=analysis.id,
        language=analysis.language,
        language_confidence=analysis.language_confidence,
        clause_count=analysis.clause_count,
        risk_level=analysis.risk_level,
        compliance_score=analysis.compliance_score,
        model_used=analysis.model_used,
        created_at=analysis.created_at,
        clauses=clauses,
    )


@router.get("/{document_id}/analysis/summary", response_model=NLPAnalysisSummaryResponse)
def get_document_analysis_summary(document_id: int, db: Session = Depends(get_db)) -> NLPAnalysisSummaryResponse:
    """Get analysis summary (no clause text — lightweight)."""
    _get_document_or_404(document_id, db)
    analysis = _get_analysis_or_404(document_id, db)
    return NLPAnalysisSummaryResponse(
        document_id=document_id,
        analysis_id=analysis.id,
        language=analysis.language,
        language_confidence=analysis.language_confidence,
        clause_count=analysis.clause_count,
        risk_level=analysis.risk_level,
        compliance_score=analysis.compliance_score,
        model_used=analysis.model_used,
        created_at=analysis.created_at,
    )


@router.get("/{document_id}/clauses", response_model=ClauseListResponse)
def get_document_clauses(
    document_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    label: str | None = Query(default=None, description="Filter by clause label"),
    flag: str | None = Query(default=None, description="Filter by compliance flag"),
    db: Session = Depends(get_db),
) -> ClauseListResponse:
    """Get paginated clause list with optional label/flag filters."""
    _get_document_or_404(document_id, db)
    analysis = _get_analysis_or_404(document_id, db)
    all_clauses = analysis.get_clauses()

    # Apply filters
    if label:
        all_clauses = [c for c in all_clauses if label in c.get("labels", [])]
    if flag:
        all_clauses = [c for c in all_clauses if flag in c.get("compliance_flags", [])]

    total = len(all_clauses)
    page = all_clauses[offset: offset + limit]

    return ClauseListResponse(
        document_id=document_id,
        total_count=total,
        items=[_build_clause_schema(c) for c in page],
    )


@router.get("/{document_id}/clauses/{clause_id}", response_model=ClauseDetailResponse)
def get_clause_detail(document_id: int, clause_id: str, db: Session = Depends(get_db)) -> ClauseDetailResponse:
    """Get a single clause by its ID."""
    _get_document_or_404(document_id, db)
    analysis = _get_analysis_or_404(document_id, db)
    clauses = {c["clause_id"]: c for c in analysis.get_clauses()}
    if clause_id not in clauses:
        raise HTTPException(status_code=404, detail={"code": "clause_not_found", "message": f"Clause {clause_id} not found"})
    return ClauseDetailResponse(document_id=document_id, clause=_build_clause_schema(clauses[clause_id]))


class AnalyzeTriggerResponse(BaseModel):
    document_id: int
    task_id: str | None
    message: str


@router.post("/{document_id}/analyze", response_model=AnalyzeTriggerResponse, status_code=202)
def trigger_nlp_analysis(document_id: int, db: Session = Depends(get_db)) -> AnalyzeTriggerResponse:
    """
    Manually trigger (or re-trigger) NLP analysis for a document.
    The document must be in 'extracted' or 'analyzed' status.
    """
    from app.core.config import STATUS_ANALYZED, STATUS_EXTRACTED
    from app.tasks.nlp_analysis import enqueue_nlp_analysis

    doc = _get_document_or_404(document_id, db)
    if doc.status not in {STATUS_EXTRACTED, STATUS_ANALYZED}:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "invalid_state",
                "message": f"Cannot analyze document in status '{doc.status}'. Must be 'extracted' or 'analyzed'.",
            },
        )
    task_id = enqueue_nlp_analysis(document_id)
    return AnalyzeTriggerResponse(
        document_id=document_id,
        task_id=task_id,
        message="NLP analysis queued.",
    )
