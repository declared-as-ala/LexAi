"""Celery task for Agent 3 — Legal Evaluation."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import (
    STAGE_EVAL_COMPLETED,
    STAGE_EVAL_PERSISTING,
    STAGE_EVAL_RULES,
    STAGE_EVAL_SCORING,
    STAGE_EVALUATING,
    STATUS_ANALYZED,
    STATUS_EVALUATED,
    STATUS_EVALUATING,
    STATUS_FAILED,
)
from app.core.logging import get_logger
from app.db.models.document import Document
from app.db.models.evaluation import Evaluation
from app.db.models.nlp_analysis import NLPAnalysis
from app.db.session import SessionLocal
from app.legal.rule_engine import evaluate
from app.legal.scorer import compute_scores
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


def run_evaluation_sync(document_id: int) -> dict[str, object]:
    """Run legal evaluation synchronously. Called by Celery worker or directly."""
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return {"ok": False, "error": f"Document {document_id} not found"}

        # Load NLP analysis
        analysis = (
            db.query(NLPAnalysis)
            .filter(NLPAnalysis.document_id == document_id)
            .order_by(NLPAnalysis.id.desc())
            .first()
        )
        if not analysis:
            return {"ok": False, "error": "No NLP analysis found — run Agent 2 first"}

        clauses = analysis.get_clauses()
        if not clauses:
            return {"ok": False, "error": "NLP analysis has no clauses"}

        # Mark as evaluating
        _set_status(db, document_id, STATUS_EVALUATING, STAGE_EVALUATING, "Starting legal evaluation…", 0)

        # 1. Rule matching
        _set_status(db, document_id, STATUS_EVALUATING, STAGE_EVAL_RULES, "Matching legal rules…", 30)
        eval_result = evaluate(clauses)

        logger.info(
            "eval_task_rules_matched",
            extra={"extra": {
                "document_id": document_id,
                "violations": len(eval_result.violations),
                "missing_clauses": len(eval_result.missing_clause_keys),
                "active_frameworks": eval_result.active_frameworks,
            }},
        )

        # 2. Scoring
        _set_status(db, document_id, STATUS_EVALUATING, STAGE_EVAL_SCORING, "Computing compliance scores…", 60)
        score_result = compute_scores(eval_result.violations, eval_result.active_frameworks)

        logger.info(
            "eval_task_scores",
            extra={"extra": {
                "document_id": document_id,
                "global_score": score_result.global_score,
                "litigation_risk": score_result.litigation_risk,
                "framework_scores": score_result.framework_scores,
            }},
        )

        # 3. Persist
        _set_status(db, document_id, STATUS_EVALUATING, STAGE_EVAL_PERSISTING, "Saving evaluation…", 85)

        # Serialize violations to dicts
        violation_dicts = [
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

        # Remove any previous evaluation for this document
        db.query(Evaluation).filter(Evaluation.document_id == document_id).delete()

        evaluation = Evaluation(
            document_id=document_id,
            global_score=score_result.global_score,
            litigation_risk=score_result.litigation_risk,
            lnpdp_score=score_result.framework_scores.get("LNPDP"),
            gdpr_score=score_result.framework_scores.get("GDPR"),
            iso27001_score=score_result.framework_scores.get("ISO27001"),
            iso9001_score=score_result.framework_scores.get("ISO9001"),
            evaluated_at=datetime.now(timezone.utc),
        )
        evaluation.set_violations(violation_dicts)
        evaluation.set_missing_clauses(eval_result.missing_clause_keys)
        evaluation.set_active_frameworks(eval_result.active_frameworks)
        evaluation.set_violation_counts(score_result.framework_violation_counts)
        db.add(evaluation)

        # Mark document as evaluated
        _set_status(
            db, document_id,
            STATUS_EVALUATED, STAGE_EVAL_COMPLETED,
            f"Evaluation complete — {len(eval_result.violations)} violations found — score {score_result.global_score:.0f}/100",
            100,
        )
        db.commit()

        try:
            from app.tasks.recommendation import enqueue_recommendation

            enqueue_recommendation(document_id)
        except Exception as rec_exc:
            logger.warning(
                "eval_task_recommend_chain_failed",
                extra={"extra": {"document_id": document_id, "error": str(rec_exc)}},
            )

        return {
            "ok": True,
            "document_id": document_id,
            "global_score": score_result.global_score,
            "litigation_risk": score_result.litigation_risk,
            "violation_count": len(eval_result.violations),
        }

    except Exception as exc:
        db.rollback()
        doc = db.get(Document, document_id)
        if doc:
            doc.status = STATUS_FAILED
            doc.progress_stage = "failed"
            doc.last_error = str(exc)
            db.commit()
        logger.exception("eval_task_failed", extra={"extra": {"document_id": document_id, "error": str(exc)}})
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.evaluation.run_evaluation")
def run_evaluation(document_id: int) -> dict[str, object]:
    """Celery task entrypoint for Agent 3."""
    return run_evaluation_sync(document_id)


def enqueue_evaluation(document_id: int) -> str | None:
    """Queue evaluation; fall back to sync if broker unavailable."""
    try:
        result = run_evaluation.delay(document_id)
        return result.id
    except Exception:
        run_evaluation_sync(document_id)
        return None
