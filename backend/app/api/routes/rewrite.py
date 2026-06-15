"""Contract rewrite review, generation, and export."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import STATUS_COMPLETE, STATUS_EVALUATED, UPLOAD_DIR
from app.db.models.document import Document, Extraction
from app.db.models.nlp_analysis import NLPAnalysis
from app.db.models.recommendation import Recommendation
from app.db.models.rewrite import (
    DECISION_ACCEPTED,
    DECISION_KEEP_ORIGINAL,
    DECISION_PENDING,
    DECISION_REJECTED,
    EXPORT_KIND_DOCX,
    EXPORT_KIND_PDF,
    REWRITE_STATUS_DRAFT,
    REWRITE_STATUS_FINALIZED,
    RewriteClauseDecision,
    RewriteExport,
    RewriteSession,
)
from app.schemas.rewrite import (
    RecommendationIdBody,
    RewriteDecisionItemSchema,
    RewriteFinalResponse,
    RewriteGenerateResponse,
    RewriteSessionSummarySchema,
    RewritesListResponse,
)
from app.services.rewrite.docx_export import build_docx_bytes, revision_summary_lines
from app.services.rewrite.engine import build_revision_metadata, build_revised_text
from app.services.rewrite.export_clean import display_title_from_filename
from app.services.rewrite.pdf_export import build_pdf_bytes

router = APIRouter(prefix="/documents", tags=["rewrites"])


def _get_document_or_404(document_id: int, db: Session) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})
    return doc


def _latest_extraction(db: Session, document_id: int) -> Extraction | None:
    return (
        db.query(Extraction)
        .filter(Extraction.document_id == document_id)
        .order_by(Extraction.id.desc())
        .first()
    )


def _latest_nlp(db: Session, document_id: int) -> NLPAnalysis | None:
    return (
        db.query(NLPAnalysis)
        .filter(NLPAnalysis.document_id == document_id)
        .order_by(NLPAnalysis.id.desc())
        .first()
    )


def _list_recommendations(db: Session, document_id: int) -> list[Recommendation]:
    return (
        db.query(Recommendation)
        .filter(Recommendation.document_id == document_id)
        .order_by(Recommendation.priority.asc(), Recommendation.id.asc())
        .all()
    )


def _clause_text_map(nlp: NLPAnalysis | None) -> dict[str, str]:
    if not nlp:
        return {}
    out: dict[str, str] = {}
    for c in nlp.get_clauses():
        cid = c.get("clause_id")
        if cid:
            out[str(cid)] = str(c.get("text") or "")
    return out


def _flags_map(nlp: NLPAnalysis | None) -> dict[str, list[str]]:
    if not nlp:
        return {}
    out: dict[str, list[str]] = {}
    for c in nlp.get_clauses():
        cid = c.get("clause_id")
        if cid:
            flags = c.get("compliance_flags") or []
            out[str(cid)] = [str(f) for f in flags]
    return out


def _seed_decisions(db: Session, session: RewriteSession, recs: list[Recommendation]) -> None:
    existing = {d.recommendation_id for d in session.decisions}
    for r in recs:
        if r.id in existing:
            continue
        db.add(
            RewriteClauseDecision(
                session_id=session.id,
                recommendation_id=r.id,
                clause_id=r.clause_id,
                decision=DECISION_PENDING,
            )
        )


def _get_or_create_draft_session(db: Session, document_id: int) -> RewriteSession:
    latest = (
        db.query(RewriteSession)
        .filter(RewriteSession.document_id == document_id)
        .order_by(RewriteSession.id.desc())
        .first()
    )
    recs = _list_recommendations(db, document_id)
    if latest is None or latest.status == REWRITE_STATUS_FINALIZED:
        sess = RewriteSession(document_id=document_id, status=REWRITE_STATUS_DRAFT)
        db.add(sess)
        db.flush()
        _seed_decisions(db, sess, recs)
        db.commit()
        db.refresh(sess)
        return sess
    _seed_decisions(db, latest, recs)
    db.commit()
    db.refresh(latest)
    return latest


def _decision_map(db: Session, session_id: int) -> dict[int, str]:
    rows = db.query(RewriteClauseDecision).filter(RewriteClauseDecision.session_id == session_id).all()
    return {r.recommendation_id: r.decision for r in rows}


def _recommendation_dicts(recs: list[Recommendation]) -> list[dict]:
    return [
        {
            "id": r.id,
            "clause_id": r.clause_id,
            "priority": r.priority,
            "rewritten_clause": r.rewritten_clause,
        }
        for r in recs
    ]


def _clear_other_accepts_for_clause(
    db: Session, session_id: int, clause_id: str, keep_recommendation_id: int
) -> None:
    rec_ids_for_clause = (
        db.query(RewriteClauseDecision.recommendation_id)
        .join(Recommendation, Recommendation.id == RewriteClauseDecision.recommendation_id)
        .filter(
            RewriteClauseDecision.session_id == session_id,
            Recommendation.clause_id == clause_id,
            RewriteClauseDecision.recommendation_id != keep_recommendation_id,
        )
        .all()
    )
    for (rid,) in rec_ids_for_clause:
        row = (
            db.query(RewriteClauseDecision)
            .filter(
                RewriteClauseDecision.session_id == session_id,
                RewriteClauseDecision.recommendation_id == rid,
            )
            .first()
        )
        if row and row.decision == DECISION_ACCEPTED:
            row.decision = DECISION_REJECTED


@router.get("/{document_id}/rewrites", response_model=RewritesListResponse)
def get_rewrites(document_id: int, db: Session = Depends(get_db)) -> RewritesListResponse:
    _get_document_or_404(document_id, db)
    sess = _get_or_create_draft_session(db, document_id)
    nlp = _latest_nlp(db, document_id)
    texts = _clause_text_map(nlp)
    flags = _flags_map(nlp)
    recs = _list_recommendations(db, document_id)
    by_rec = {d.recommendation_id: d for d in sess.decisions}
    items: list[RewriteDecisionItemSchema] = []
    for r in recs:
        d = by_rec.get(r.id)
        decision = d.decision if d else DECISION_PENDING
        cid = r.clause_id
        items.append(
            RewriteDecisionItemSchema(
                recommendation_id=r.id,
                clause_id=cid,
                decision=decision,
                rewritten_clause=r.rewritten_clause,
                issue_description=r.issue_description,
                severity=r.severity,
                priority=r.priority,
                framework=r.framework,
                article=r.article,
                legal_rationale=r.legal_rationale,
                original_clause_text=texts.get(cid or "", None),
                compliance_flags=flags.get(cid or "", []),
            )
        )
    return RewritesListResponse(
        document_id=document_id,
        session=RewriteSessionSummarySchema.model_validate(sess),
        items=items,
    )


def _resolve_rec_for_clause(
    db: Session, document_id: int, clause_id: str, recommendation_id: int | None
) -> Recommendation:
    recs = _list_recommendations(db, document_id)
    matching = [r for r in recs if (r.clause_id or "") == clause_id]
    if not matching:
        raise HTTPException(
            status_code=404,
            detail={"code": "no_recommendations", "message": f"No recommendations for clause {clause_id}"},
        )
    if recommendation_id is not None:
        rec = next((r for r in matching if r.id == recommendation_id), None)
        if not rec:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Recommendation not found"})
        return rec
    return matching[0]


@router.post("/{document_id}/rewrites/{clause_id}/accept")
def accept_rewrite(
    document_id: int,
    clause_id: str,
    body: RecommendationIdBody | None = Body(None),
    db: Session = Depends(get_db),
) -> dict:
    _get_document_or_404(document_id, db)
    sess = _get_or_create_draft_session(db, document_id)
    if sess.status != REWRITE_STATUS_DRAFT:
        raise HTTPException(status_code=409, detail={"code": "session_locked", "message": "Finalize a new draft first"})
    payload = body or RecommendationIdBody()
    rid = payload.recommendation_id
    rec = _resolve_rec_for_clause(db, document_id, clause_id, rid)
    row = (
        db.query(RewriteClauseDecision)
        .filter(
            RewriteClauseDecision.session_id == sess.id,
            RewriteClauseDecision.recommendation_id == rec.id,
        )
        .first()
    )
    if not row:
        row = RewriteClauseDecision(
            session_id=sess.id,
            recommendation_id=rec.id,
            clause_id=rec.clause_id,
            decision=DECISION_PENDING,
        )
        db.add(row)
        db.flush()
    row.decision = DECISION_ACCEPTED
    row.clause_id = rec.clause_id
    _clear_other_accepts_for_clause(db, sess.id, clause_id, rec.id)
    db.commit()
    return {"ok": True, "recommendation_id": rec.id, "decision": DECISION_ACCEPTED}


@router.post("/{document_id}/rewrites/{clause_id}/reject")
def reject_rewrite(
    document_id: int,
    clause_id: str,
    body: RecommendationIdBody | None = Body(None),
    db: Session = Depends(get_db),
) -> dict:
    _get_document_or_404(document_id, db)
    sess = _get_or_create_draft_session(db, document_id)
    if sess.status != REWRITE_STATUS_DRAFT:
        raise HTTPException(status_code=409, detail={"code": "session_locked", "message": "Finalize a new draft first"})
    payload = body or RecommendationIdBody()
    rid = payload.recommendation_id
    if rid is not None:
        rec = db.get(Recommendation, rid)
        if not rec or rec.document_id != document_id or (rec.clause_id or "") != clause_id:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Recommendation not found"})
        targets = [rec.id]
    else:
        targets = [r.id for r in _list_recommendations(db, document_id) if (r.clause_id or "") == clause_id]
    for tid in targets:
        row = (
            db.query(RewriteClauseDecision)
            .filter(
                RewriteClauseDecision.session_id == sess.id,
                RewriteClauseDecision.recommendation_id == tid,
            )
            .first()
        )
        if row:
            row.decision = DECISION_REJECTED
    db.commit()
    return {"ok": True, "updated_recommendation_ids": targets}


@router.post("/{document_id}/rewrites/{clause_id}/keep-original")
def keep_original(
    document_id: int,
    clause_id: str,
    body: RecommendationIdBody | None = Body(None),
    db: Session = Depends(get_db),
) -> dict:
    _get_document_or_404(document_id, db)
    sess = _get_or_create_draft_session(db, document_id)
    if sess.status != REWRITE_STATUS_DRAFT:
        raise HTTPException(status_code=409, detail={"code": "session_locked", "message": "Finalize a new draft first"})
    payload = body or RecommendationIdBody()
    rid = payload.recommendation_id
    if rid is not None:
        rec = db.get(Recommendation, rid)
        if not rec or rec.document_id != document_id or (rec.clause_id or "") != clause_id:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Recommendation not found"})
        targets = [rec.id]
    else:
        targets = [r.id for r in _list_recommendations(db, document_id) if (r.clause_id or "") == clause_id]
    for tid in targets:
        row = (
            db.query(RewriteClauseDecision)
            .filter(
                RewriteClauseDecision.session_id == sess.id,
                RewriteClauseDecision.recommendation_id == tid,
            )
            .first()
        )
        if row:
            row.decision = DECISION_KEEP_ORIGINAL
    db.commit()
    return {"ok": True, "updated_recommendation_ids": targets}


@router.post("/{document_id}/rewrites/generate", response_model=RewriteGenerateResponse)
def generate_revised(document_id: int, db: Session = Depends(get_db)) -> RewriteGenerateResponse:
    doc = _get_document_or_404(document_id, db)
    if doc.status not in {STATUS_COMPLETE, STATUS_EVALUATED}:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "pipeline_incomplete",
                "message": "Document must be evaluated or complete before generating a revision",
            },
        )
    extraction = _latest_extraction(db, document_id)
    if not extraction or not (extraction.normalized_text or "").strip():
        raise HTTPException(status_code=409, detail={"code": "no_extraction", "message": "Missing normalized text"})
    nlp = _latest_nlp(db, document_id)
    if not nlp:
        raise HTTPException(status_code=409, detail={"code": "no_analysis", "message": "Missing NLP analysis"})
    clauses = nlp.get_clauses()
    if not clauses:
        raise HTTPException(status_code=409, detail={"code": "no_clauses", "message": "No clauses to revise"})

    sess = _get_or_create_draft_session(db, document_id)
    if sess.status != REWRITE_STATUS_DRAFT:
        raise HTTPException(status_code=409, detail={"code": "session_locked", "message": "No active draft session"})

    recs = _list_recommendations(db, document_id)
    decision_by = _decision_map(db, sess.id)
    rec_dicts = _recommendation_dicts(recs)
    final_text = build_revised_text(extraction.normalized_text, clauses, rec_dicts, decision_by)
    meta = build_revision_metadata(extraction.normalized_text, clauses, rec_dicts, decision_by)
    changed = sum(1 for m in meta if m.get("changed"))

    sess.final_text = final_text
    sess.revision_metadata_json = json.dumps(meta, ensure_ascii=False)
    sess.status = REWRITE_STATUS_FINALIZED
    db.commit()

    return RewriteGenerateResponse(
        document_id=document_id,
        session_id=sess.id,
        status=sess.status,
        final_text_length=len(final_text),
        changed_clauses=changed,
        message="Revision générée. Créez une nouvelle session via GET /rewrites pour ajuster.",
    )


@router.get("/{document_id}/rewrites/final", response_model=RewriteFinalResponse)
def get_final_rewrite(document_id: int, db: Session = Depends(get_db)) -> RewriteFinalResponse:
    _get_document_or_404(document_id, db)
    sess = (
        db.query(RewriteSession)
        .filter(RewriteSession.document_id == document_id, RewriteSession.status == REWRITE_STATUS_FINALIZED)
        .order_by(RewriteSession.id.desc())
        .first()
    )
    if not sess or not sess.final_text:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "No finalized revision yet"})
    meta: list = []
    if sess.revision_metadata_json:
        try:
            meta = json.loads(sess.revision_metadata_json)
        except json.JSONDecodeError:
            meta = []
    exports = (
        db.query(RewriteExport)
        .filter(RewriteExport.session_id == sess.id)
        .order_by(RewriteExport.id.desc())
        .all()
    )
    export_payload = [
        {"id": e.id, "kind": e.kind, "file_path": e.file_path, "size_bytes": e.size_bytes, "created_at": e.created_at.isoformat()}
        for e in exports
    ]
    return RewriteFinalResponse(
        document_id=document_id,
        session_id=sess.id,
        final_text=sess.final_text,
        revision_metadata=meta,
        exports=export_payload,
    )


def _export_dir(document_id: int, session_id: int) -> Path:
    return UPLOAD_DIR / "exports" / str(document_id) / str(session_id)


def _run_export(
    db: Session,
    doc: Document,
    session_id: int,
    kind: str,
) -> RewriteExport:
    sess = db.get(RewriteSession, session_id)
    if not sess or sess.document_id != doc.id or sess.status != REWRITE_STATUS_FINALIZED:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Finalized session not found"})
    if not sess.final_text:
        raise HTTPException(status_code=409, detail={"code": "no_text", "message": "Session has no final text"})

    meta_list: list = []
    if sess.revision_metadata_json:
        try:
            meta_list = json.loads(sess.revision_metadata_json)
        except json.JSONDecodeError:
            meta_list = []

    display_title = display_title_from_filename(doc.name or f"Document_{doc.id}")
    export_date = (
        doc.finished_at.strftime("%Y-%m-%d")
        if doc.finished_at
        else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    if kind == EXPORT_KIND_DOCX:
        summary = revision_summary_lines(meta_list)
        blob = build_docx_bytes(
            display_title,
            sess.final_text,
            summary,
            export_date=export_date,
            revision_metadata=meta_list,
        )
        ext = "docx"
    elif kind == EXPORT_KIND_PDF:
        blob = build_pdf_bytes(display_title, sess.final_text, export_date=export_date)
        ext = "pdf"
    else:
        raise HTTPException(status_code=400, detail={"code": "bad_kind", "message": f"Unknown export kind {kind}"})

    out_dir = _export_dir(doc.id, sess.id)
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"revised_{sess.id}.{ext}"
    path = out_dir / fname
    path.write_bytes(blob)

    row = RewriteExport(session_id=sess.id, kind=kind, file_path=str(path), size_bytes=len(blob))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/{document_id}/exports/docx")
def export_docx(
    document_id: int,
    session_id: int | None = Query(None, description="Finalized rewrite session id; defaults to latest"),
    db: Session = Depends(get_db),
) -> FileResponse:
    doc = _get_document_or_404(document_id, db)
    if session_id is None:
        sess = (
            db.query(RewriteSession)
            .filter(RewriteSession.document_id == document_id, RewriteSession.status == REWRITE_STATUS_FINALIZED)
            .order_by(RewriteSession.id.desc())
            .first()
        )
        if not sess:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "No finalized session"})
        session_id = sess.id
    export = _run_export(db, doc, session_id, EXPORT_KIND_DOCX)
    return FileResponse(
        export.file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"revised_{document_id}_{export.id}.docx",
    )


@router.post("/{document_id}/exports/pdf")
def export_pdf(
    document_id: int,
    session_id: int | None = Query(None, description="Finalized rewrite session id; defaults to latest"),
    db: Session = Depends(get_db),
) -> FileResponse:
    doc = _get_document_or_404(document_id, db)
    if session_id is None:
        sess = (
            db.query(RewriteSession)
            .filter(RewriteSession.document_id == document_id, RewriteSession.status == REWRITE_STATUS_FINALIZED)
            .order_by(RewriteSession.id.desc())
            .first()
        )
        if not sess:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "No finalized session"})
        session_id = sess.id
    export = _run_export(db, doc, session_id, EXPORT_KIND_PDF)
    return FileResponse(
        export.file_path,
        media_type="application/pdf",
        filename=f"revised_{document_id}_{export.id}.pdf",
    )
