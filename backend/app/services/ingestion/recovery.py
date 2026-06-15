"""Recovery helpers for interrupted Agent 1 processing runs."""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.models.document import Document
from app.services.ingestion.progress import DocumentProgressService

logger = get_logger(__name__)


def recover_interrupted_documents(session) -> int:
    """Mark stale in-progress documents as failed after a restart.

    This prevents the UI from showing permanently queued items when older tasks
    were discarded during a previous broken worker/backend run.
    """
    stuck_statuses = ("queued", "extracting", "analyzing", "evaluating", "recommending")
    stuck_documents = (
        session.query(Document)
        .filter(Document.status.in_(stuck_statuses))
        .all()
    )

    progress = DocumentProgressService(session)
    recovered = 0
    for document in stuck_documents:
        progress.failed(
            document.id,
            document.last_error or "Processing was interrupted during a previous run. Please retry the pipeline.",
            percent=document.progress_percent,
        )
        recovered += 1

    if recovered:
        logger.info(
            "recovered_interrupted_documents",
            extra={"extra": {"count": recovered}},
        )
    return recovered
