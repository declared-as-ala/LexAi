"""
LangGraph node: nlp_analyze_document (Agent 2).
Reads extraction from DB, runs NLP pipeline, persists NLPAnalysis to DB,
returns state update with 'clauses' and 'entities'.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.models.document import Extraction
from app.db.models.nlp_analysis import NLPAnalysis
from app.db.session import SessionLocal
from app.services.nlp.clause_classifier import ClauseClassifier
from app.services.nlp.clause_segmenter import ClauseSegmenter
from app.services.nlp.entity_extractor import EntityExtractor
from app.services.nlp.language_detector import LanguageDetector
from app.workflows.state import AnalysisState

logger = get_logger(__name__)


def nlp_analyze_document(state: AnalysisState) -> AnalysisState:
    """
    Agent 2 LangGraph node.
    Reads normalized_text from DB Extraction, runs the full NLP pipeline,
    persists results, and returns updated state.
    """
    doc_id = state.get("document_id")
    errors = list(state.get("errors") or [])
    audit_trace = list(state.get("audit_trace") or [])

    if doc_id is None:
        errors.append("nlp_analyze_document: document_id is required")
        return {"errors": errors, "audit_trace": audit_trace}

    db = SessionLocal()
    try:
        # Load latest extraction
        extraction = (
            db.query(Extraction)
            .filter(Extraction.document_id == doc_id)
            .order_by(Extraction.id.desc())
            .first()
        )
        if not extraction:
            errors.append(f"nlp_analyze_document: no extraction found for document {doc_id}")
            return {"errors": errors, "audit_trace": audit_trace}

        normalized_text = extraction.normalized_text or ""
        structure_json = extraction.get_structure()

        if not normalized_text.strip():
            errors.append(f"nlp_analyze_document: empty normalized_text for document {doc_id}")
            return {"errors": errors, "audit_trace": audit_trace}

        # 1. Language detection
        lang_result = LanguageDetector().detect(normalized_text)
        language = lang_result.language
        logger.info("nlp_language_detected", extra={"extra": {"document_id": doc_id, "language": language}})

        # 2. Clause segmentation
        segments = ClauseSegmenter().segment(normalized_text, structure_json)
        logger.info("nlp_clauses_segmented", extra={"extra": {"document_id": doc_id, "count": len(segments)}})

        # 3. Entity extraction
        entity_extractor = EntityExtractor(language=language)
        entities_by_clause = entity_extractor.extract_all(segments)

        # 4. Clause classification
        classifier = ClauseClassifier(language=language)
        classifications = classifier.classify_all(segments)

        # 5. Merge into clause objects
        model_used = next(
            (r.model_used for r in classifications.values() if r.model_used != "heuristic"),
            "heuristic",
        )

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

        # 6. Persist NLPAnalysis record
        analysis = NLPAnalysis(
            document_id=doc_id,
            language=language,
            language_confidence=lang_result.confidence,
            model_used=model_used,
        )
        analysis.set_clauses(clause_records)
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        audit_trace.append({
            "node": "nlp_analyze_document",
            "document_id": doc_id,
            "language": language,
            "clause_count": len(clause_records),
            "model_used": model_used,
            "status": "ok",
        })

        logger.info(
            "nlp_analysis_complete",
            extra={"extra": {"document_id": doc_id, "clauses": len(clause_records), "model": model_used}},
        )

        return {
            "clauses": clause_records,
            "errors": errors,
            "audit_trace": audit_trace,
        }

    except Exception as exc:
        errors.append(f"nlp_analyze_document: {exc}")
        audit_trace.append({
            "node": "nlp_analyze_document",
            "document_id": doc_id,
            "status": "error",
            "message": str(exc),
        })
        logger.exception("nlp_analysis_failed", extra={"extra": {"document_id": doc_id, "error": str(exc)}})
        return {"errors": errors, "audit_trace": audit_trace}
    finally:
        db.close()
