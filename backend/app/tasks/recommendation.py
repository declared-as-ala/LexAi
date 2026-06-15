"""Celery task for Agent 4 — template-based recommendations."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import (
    LLM_ENABLED,
    STAGE_REC_COMPLETED,
    STAGE_REC_LLM,
    STAGE_REC_PERSISTING,
    STAGE_REC_TEMPLATES,
    STAGE_RECOMMENDING,
    STATUS_COMPLETE,
    STATUS_FAILED,
    STATUS_RECOMMENDING,
)
from app.core.logging import get_logger
from app.db.models.document import Document
from app.db.models.evaluation import Evaluation
from app.db.models.nlp_analysis import NLPAnalysis
from app.db.models.recommendation import Recommendation
from app.db.session import SessionLocal
from app.legal.recommender import build_recommendation_rows
from app.services.llm.refine_recommendations import refine_recommendation_rows
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


def _set_status(db, document_id: int, status: str, stage: str, message: str, percent: int) -> None:
    doc = db.get(Document, document_id)
    if doc:
        doc.status = status
        doc.progress_stage = stage
        doc.progress_message = message
        doc.progress_percent = percent
        db.commit()


def run_recommendation_sync(document_id: int) -> dict[str, object]:
    """Generate and persist recommendations from the latest evaluation + NLP clauses."""
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return {"ok": False, "error": f"Document {document_id} not found"}

        evaluation = (
            db.query(Evaluation).filter(Evaluation.document_id == document_id).order_by(Evaluation.id.desc()).first()
        )
        if not evaluation:
            return {"ok": False, "error": "No evaluation found — run Agent 3 first"}

        analysis = (
            db.query(NLPAnalysis).filter(NLPAnalysis.document_id == document_id).order_by(NLPAnalysis.id.desc()).first()
        )
        if not analysis:
            return {"ok": False, "error": "No NLP analysis found — run Agent 2 first"}

        clauses = analysis.get_clauses()
        violations = evaluation.get_violations()

        _set_status(db, document_id, STATUS_RECOMMENDING, STAGE_RECOMMENDING, "Generating recommendations…", 0)
        _set_status(db, document_id, STATUS_RECOMMENDING, STAGE_REC_TEMPLATES, "Applying recommendation templates…", 40)

        rows = build_recommendation_rows(violations, clauses)

        if LLM_ENABLED:
            _set_status(
                db,
                document_id,
                STATUS_RECOMMENDING,
                STAGE_REC_LLM,
                "Refining recommendations with Groq LLM…",
                58,
            )
            rows = refine_recommendation_rows(rows, violations, clauses)

        _set_status(db, document_id, STATUS_RECOMMENDING, STAGE_REC_PERSISTING, "Saving recommendations…", 85)

        db.query(Recommendation).filter(Recommendation.document_id == document_id).delete()

        for row in rows:
            db.add(
                Recommendation(
                    document_id=document_id,
                    violation_id=row.get("violation_id"),
                    clause_id=row.get("clause_id"),
                    violation_rule_id=row.get("violation_rule_id"),
                    framework=row.get("framework"),
                    article=row.get("article"),
                    severity=row.get("severity"),
                    priority=row.get("priority"),
                    issue_description=row.get("issue_description"),
                    recommendation_text=row.get("recommendation_text"),
                    rewritten_clause=row.get("rewritten_clause"),
                    legal_rationale=row.get("legal_rationale"),
                    generated_by=row.get("generated_by"),
                )
            )

        _set_status(
            db,
            document_id,
            STATUS_COMPLETE,
            STAGE_REC_COMPLETED,
            f"Pipeline complete — {len(rows)} recommendation(s) generated",
            100,
        )
        doc = db.get(Document, document_id)
        if doc:
            doc.finished_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "recommend_task_complete",
            extra={"extra": {"document_id": document_id, "count": len(rows)}},
        )
        return {"ok": True, "document_id": document_id, "recommendation_count": len(rows)}

    except Exception as exc:
        db.rollback()
        doc = db.get(Document, document_id)
        if doc:
            doc.status = STATUS_FAILED
            doc.progress_stage = "failed"
            doc.last_error = str(exc)
            db.commit()
        logger.exception("recommend_task_failed", extra={"extra": {"document_id": document_id, "error": str(exc)}})
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.recommendation.run_recommendation")
def run_recommendation(document_id: int) -> dict[str, object]:
    """Celery task entrypoint for Agent 4."""
    return run_recommendation_sync(document_id)


def enqueue_recommendation(document_id: int) -> str | None:
    """Queue recommendation generation; fall back to sync if broker unavailable."""
    try:
        result = run_recommendation.delay(document_id)
        return result.id
    except Exception:
        run_recommendation_sync(document_id)
        return None
