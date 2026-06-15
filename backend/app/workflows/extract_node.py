"""
LangGraph node: extract_document.
Loads document from DB, runs ExtractorService, updates state with extraction_result and normalized_text.
Returns a state update dict for LangGraph to merge.
"""

from app.db.session import SessionLocal
from app.db.models.document import Document
from app.services.ingestion import ExtractorService
from app.workflows.state import AnalysisState


def extract_document(state: AnalysisState) -> AnalysisState:
    """
    Run Extractor Agent for state.document_id; return update with extraction_result and normalized_text.
    Persists extraction to DB. On error, appends to state.errors.
    """
    doc_id = state.get("document_id")
    errors = list(state.get("errors") or [])
    audit_trace = list(state.get("audit_trace") or [])
    if doc_id is None:
        errors.append("extract_document: document_id is required")
        return {"errors": errors, "audit_trace": audit_trace}
    db = SessionLocal()
    try:
        doc = db.get(Document, doc_id)
        if not doc:
            errors.append(f"extract_document: document {doc_id} not found")
            return {"errors": errors, "audit_trace": audit_trace}
        svc = ExtractorService()
        artifact = svc.run(
            document_id=doc.id,
            file_path=doc.file_path,
            mime_type=doc.mime_type,
            filename=doc.filename,
            size_bytes=doc.size_bytes,
            session=db,
        )
        extraction_result = artifact.model_dump()
        normalized_text = artifact.normalized_text or ""
        if artifact.errors:
            errors.extend(artifact.errors)
        audit_trace.append({"node": "extract_document", "document_id": doc_id, "status": "ok"})
        return {
            "extraction_result": extraction_result,
            "normalized_text": normalized_text,
            "errors": errors,
            "audit_trace": audit_trace,
        }
    except Exception as e:
        errors.append(f"extract_document: {e}")
        audit_trace.append({"node": "extract_document", "document_id": doc_id, "status": "error", "message": str(e)})
        return {"errors": errors, "audit_trace": audit_trace}
    finally:
        db.close()
