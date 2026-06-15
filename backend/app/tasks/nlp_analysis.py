"""Celery task for Agent 2 NLP analysis."""

from __future__ import annotations

from app.services.nlp.taxonomy import RiskLevel, ComplianceFlag
from app.core.config import (
    STAGE_ANALYZING,
    STAGE_CLASSIFYING,
    STAGE_NLP_COMPLETED,
    STAGE_NLP_PERSISTING,
    STAGE_SEGMENTING,
    STATUS_ANALYZED,
    STATUS_ANALYZING,
    STATUS_FAILED,
)
from app.core.logging import get_logger
from app.db.models.document import Document, Extraction
from app.db.models.nlp_analysis import NLPAnalysis
from app.db.session import SessionLocal
from app.services.nlp.clause_classifier import ClauseClassifier
from app.services.nlp.clause_segmenter import ClauseSegmenter
from app.services.nlp.entity_extractor import EntityExtractor
from app.services.nlp.language_detector import LanguageDetector
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)

# Flags that indicate high-severity violations
_HIGH_SEVERITY_FLAGS = {
    ComplianceFlag.UNLAWFUL_CROSS_BORDER_TRANSFER.value,
    ComplianceFlag.MISSING_RETENTION_PERIOD.value,
    ComplianceFlag.MISSING_CONSENT_MECHANISM.value,
}
_MEDIUM_SEVERITY_FLAGS = {
    ComplianceFlag.MISSING_SECURITY_MEASURES.value,
    ComplianceFlag.MISSING_DATA_SUBJECT_RIGHTS.value,
    ComplianceFlag.MISSING_DPO_REFERENCE.value,
}


def _compute_risk_level(clause_records: list[dict]) -> tuple[str, float]:
    """
    Derive document-level risk_level and compliance_score from clause flags.

    compliance_score: 0–100, where 100 = fully compliant (no gap flags).
    risk_level: critical / high / medium / low based on flag severity and count.
    """
    total_data_clauses = sum(
        1 for c in clause_records if "data_processing" in c.get("labels", [])
    )
    high_count = 0
    medium_count = 0
    all_flags: set[str] = set()

    for clause in clause_records:
        for flag in clause.get("compliance_flags", []):
            all_flags.add(flag)
            if flag in _HIGH_SEVERITY_FLAGS:
                high_count += 1
            elif flag in _MEDIUM_SEVERITY_FLAGS:
                medium_count += 1

    # Score: start at 100, deduct per violation
    gap_flags = {f for f in all_flags if f not in {
        ComplianceFlag.LNPDP_RELEVANT.value, ComplianceFlag.GDPR_RELEVANT.value
    }}
    max_deduction = 100.0
    deduction = min(high_count * 20 + medium_count * 10, max_deduction)
    compliance_score = round(max(0.0, 100.0 - deduction), 1)

    # Risk level
    if high_count >= 3 or compliance_score < 40:
        risk_level = RiskLevel.CRITICAL.value
    elif high_count >= 1 or compliance_score < 60:
        risk_level = RiskLevel.HIGH.value
    elif medium_count >= 2 or compliance_score < 80:
        risk_level = RiskLevel.MEDIUM.value
    else:
        risk_level = RiskLevel.LOW.value

    return risk_level, compliance_score


def _set_status(db, document_id: int, status: str, stage: str, message: str, percent: int) -> None:
    doc = db.get(Document, document_id)
    if doc:
        doc.status = status
        doc.progress_stage = stage
        doc.progress_message = message
        doc.progress_percent = percent
        db.commit()


def run_nlp_analysis_sync(document_id: int) -> dict[str, object]:
    """Run NLP analysis synchronously. Called by Celery worker or directly."""
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return {"ok": False, "error": f"Document {document_id} not found"}

        # Load latest extraction
        extraction = (
            db.query(Extraction)
            .filter(Extraction.document_id == document_id)
            .order_by(Extraction.id.desc())
            .first()
        )
        if not extraction or not extraction.normalized_text.strip():
            return {"ok": False, "error": "No extraction found or empty text"}

        normalized_text = extraction.normalized_text
        structure_json = extraction.get_structure()

        # Mark as analyzing
        _set_status(db, document_id, STATUS_ANALYZING, STAGE_ANALYZING, "Starting NLP analysis…", 0)

        # 1. Language detection
        lang_result = LanguageDetector().detect(normalized_text)
        language = lang_result.language
        logger.info("nlp_task_language", extra={"extra": {"document_id": document_id, "language": language}})

        # 2. Clause segmentation
        _set_status(db, document_id, STATUS_ANALYZING, STAGE_SEGMENTING, "Segmenting clauses…", 20)
        segments = ClauseSegmenter().segment(normalized_text, structure_json)
        logger.info("nlp_task_segmented", extra={"extra": {"document_id": document_id, "clauses": len(segments)}})

        # 3. Entity extraction
        entity_extractor = EntityExtractor(language=language)
        entities_by_clause = entity_extractor.extract_all(segments)

        # 4. Clause classification
        _set_status(db, document_id, STATUS_ANALYZING, STAGE_CLASSIFYING, "Classifying clauses…", 60)
        classifier = ClauseClassifier(language=language)
        classifications = classifier.classify_all(segments)

        model_used = next(
            (r.model_used for r in classifications.values() if r.model_used not in ("heuristic", "none")),
            "heuristic",
        )

        # 5. Merge clause records
        clause_records: list[dict] = []
        for seg in segments:
            clf = classifications.get(seg.clause_id)
            ents = entities_by_clause.get(seg.clause_id, [])
            clause_records.append({
                "clause_id": seg.clause_id,
                "text": seg.text,
                "start_char": seg.start_char,
                "end_char": seg.end_char,
                "section_title": seg.section_title,
                "source": seg.source,
                "labels": clf.labels if clf else [],
                "compliance_flags": clf.compliance_flags if clf else [],
                "entities": [
                    {
                        "text": e.text,
                        "label": e.label,
                        "start": e.start,
                        "end": e.end,
                        "confidence": e.confidence,
                        "source": e.source,
                    }
                    for e in ents
                ],
                "confidence": clf.confidence if clf else 0.0,
                "model_used": clf.model_used if clf else "none",
            })

        # 6. Persist
        _set_status(db, document_id, STATUS_ANALYZING, STAGE_NLP_PERSISTING, "Saving analysis…", 90)

        risk_level, compliance_score = _compute_risk_level(clause_records)

        # Remove any previous analysis for this document
        db.query(NLPAnalysis).filter(NLPAnalysis.document_id == document_id).delete()

        analysis = NLPAnalysis(
            document_id=document_id,
            language=language,
            language_confidence=lang_result.confidence,
            risk_level=risk_level,
            compliance_score=compliance_score,
            model_used=model_used,
        )
        analysis.set_clauses(clause_records)
        db.add(analysis)

        # Mark document as analyzed
        _set_status(
            db, document_id,
            STATUS_ANALYZED, STAGE_NLP_COMPLETED,
            f"Analysis complete — {len(clause_records)} clauses found",
            100,
        )
        db.commit()

        logger.info(
            "nlp_task_complete",
            extra={"extra": {"document_id": document_id, "clauses": len(clause_records), "model": model_used}},
        )

        # Chain Agent 3 evaluation
        try:
            from app.tasks.evaluation import enqueue_evaluation
            enqueue_evaluation(document_id)
        except Exception as eval_exc:
            logger.warning(
                "nlp_task_eval_chain_failed",
                extra={"extra": {"document_id": document_id, "error": str(eval_exc)}},
            )

        return {"ok": True, "document_id": document_id, "clause_count": len(clause_records)}

    except Exception as exc:
        db.rollback()
        doc = db.get(Document, document_id)
        if doc:
            doc.status = STATUS_FAILED
            doc.progress_stage = "failed"
            doc.last_error = str(exc)
            db.commit()
        logger.exception("nlp_task_failed", extra={"extra": {"document_id": document_id, "error": str(exc)}})
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.nlp_analysis.run_nlp_analysis")
def run_nlp_analysis(document_id: int) -> dict[str, object]:
    """Celery task entrypoint for Agent 2."""
    return run_nlp_analysis_sync(document_id)


def enqueue_nlp_analysis(document_id: int) -> str | None:
    """Queue NLP analysis; fall back to sync if broker unavailable."""
    try:
        result = run_nlp_analysis.delay(document_id)
        return result.id
    except Exception:
        run_nlp_analysis_sync(document_id)
        return None
