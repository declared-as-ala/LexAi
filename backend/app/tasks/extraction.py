"""Celery extraction task wiring for Agent 1.
After successful extraction, automatically enqueues Agent 2 NLP analysis.
"""

from __future__ import annotations

from app.core.config import STAGE_STARTING, STATUS_FAILED
from app.core.logging import get_logger
from app.db.models.document import Document
from app.db.session import SessionLocal
from app.services.ingestion import ExtractorService
from app.services.ingestion.progress import DocumentProgressService
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


def run_extraction_sync(document_id: int) -> dict[str, object]:
    """Run extraction synchronously; used by tests and Celery worker."""
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if not document:
            return {"ok": False, "error": "Document not found"}

        progress = DocumentProgressService(db)
        progress.extracting(document_id, STAGE_STARTING, "Worker started extraction")

        service = ExtractorService()
        artifact = service.run(
            document_id=document.id,
            file_path=document.file_path,
            mime_type=document.mime_type,
            filename=document.filename,
            size_bytes=document.size_bytes,
            session=db,
        )
        result = {"ok": len(artifact.errors) == 0, "document_id": document_id, "errors": artifact.errors}

        # Chain to Agent 2 on success
        if result["ok"]:
            from app.tasks.nlp_analysis import enqueue_nlp_analysis
            enqueue_nlp_analysis(document_id)

        return result
    except Exception as exc:
        document = db.get(Document, document_id)
        if document:
            DocumentProgressService(db).failed(document_id, str(exc), percent=document.progress_percent)
        logger.exception("extraction_task_failed", extra={"extra": {"document_id": document_id}})
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.extraction.run_extraction")
def run_extraction(document_id: int) -> dict[str, object]:
    """Celery task entrypoint."""
    return run_extraction_sync(document_id)


def enqueue_extraction(document_id: int) -> str | None:
    """Queue extraction in Celery and return task id; fall back to sync when broker is unavailable."""
    try:
        async_result = run_extraction.delay(document_id)
        return async_result.id
    except Exception:
        run_extraction_sync(document_id)
        return None
