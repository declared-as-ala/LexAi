"""Document upload and extraction endpoints for Agent 1."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_UPLOAD_MB,
    STATUS_ANALYZED,
    STATUS_ANALYZING,
    STATUS_COMPLETE,
    STATUS_EVALUATED,
    STATUS_EVALUATING,
    STATUS_EXTRACTED,
    STATUS_EXTRACTING,
    STATUS_FAILED,
    STATUS_QUEUED,
    STATUS_RECOMMENDING,
)
from app.core.logging import get_logger
from app.db.models.document import Document, Extraction
from app.schemas.document import (
    DocumentBaseResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentMetadataSchema,
    DocumentSummaryResponse,
    ExtractionPayload,
    ExtractionResponse,
    RetryDocumentResponse,
    UploadDocumentResponse,
)
from app.services.ingestion.progress import DocumentProgressService
from app.services.ingestion.storage import save_upload, delete_stored_file
from app.tasks.extraction import enqueue_extraction

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)


def _validate_upload(file: UploadFile, size_bytes: int) -> None:
    extension = Path(file.filename or "").suffix.lower()
    if not file.content_type or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_mime_type",
                "message": f"Unsupported file type: {file.content_type}",
            },
        )
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_extension",
                "message": f"Unsupported file extension: {extension}",
            },
        )
    if size_bytes > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "file_too_large",
                "message": f"File too large. Max {MAX_UPLOAD_MB} MB.",
            },
        )


def _serialize_extraction(document: Document, extraction: Extraction) -> ExtractionPayload:
    return ExtractionPayload(
        document_metadata=DocumentMetadataSchema(
            filename=document.filename,
            mime_type=document.mime_type,
            size_bytes=document.size_bytes,
        ),
        raw_text=extraction.raw_text or "",
        normalized_text=extraction.normalized_text or "",
        structure=extraction.get_structure(),
        page_metadata=extraction.get_page_metadata(),
        warnings=extraction.get_warnings(),
        errors=[extraction.error_message] if extraction.error_message else [],
    )


def process_contract_upload(file: UploadFile, db: Session) -> UploadDocumentResponse:
    """Shared upload handler for ``POST /documents/upload`` and ``POST /upload-contract``."""
    try:
        contents = file.file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "read_error", "message": f"Cannot read file: {exc}"},
        ) from exc

    size_bytes = len(contents)
    _validate_upload(file, size_bytes)
    saved_path = save_upload(file, contents)

    document = Document(
        user_id=None,
        name=file.filename or "document",
        filename=file.filename or "document",
        file_path=str(saved_path),
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        status=STATUS_QUEUED,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    progress = DocumentProgressService(db)
    progress.queued(document.id, "File uploaded successfully. Task queued for extraction")

    task_id = enqueue_extraction(document.id)
    if task_id:
        document = db.get(Document, document.id)
        if document is not None:
            document.task_id = task_id
            db.commit()
            db.refresh(document)

    logger.info(
        "document_uploaded",
        extra={
            "extra": {
                "document_id": document.id,
                "filename": document.filename,
                "mime_type": document.mime_type,
                "status": document.status,
            }
        },
    )
    return UploadDocumentResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        progress_percent=document.progress_percent,
        progress_stage=document.progress_stage,
        progress_message=document.progress_message,
    )


@router.post("/upload", response_model=UploadDocumentResponse, status_code=201)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> UploadDocumentResponse:
    """Store a document, create its DB record, and enqueue extraction."""
    return process_contract_upload(file, db)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    """List uploaded documents, newest first, with persisted progress fields."""
    query = db.query(Document).order_by(Document.created_at.desc(), Document.id.desc())
    total_count = query.count()
    items = query.offset(offset).limit(limit).all()
    return DocumentListResponse(
        items=[DocumentBaseResponse.model_validate(item) for item in items],
        total_count=total_count,
    )


@router.get("/summary", response_model=DocumentSummaryResponse)
def get_documents_summary(db: Session = Depends(get_db)) -> DocumentSummaryResponse:
    """Return queue and processing summary counts from persisted backend state."""
    rows = (
        db.query(Document.status, func.count(Document.id))
        .group_by(Document.status)
        .all()
    )
    counts = {status: count for status, count in rows}
    total_count = sum(counts.values())
    extracted_or_beyond = (
        counts.get(STATUS_EXTRACTED, 0)
        + counts.get(STATUS_ANALYZING, 0)
        + counts.get(STATUS_ANALYZED, 0)
        + counts.get(STATUS_EVALUATING, 0)
        + counts.get(STATUS_EVALUATED, 0)
        + counts.get(STATUS_RECOMMENDING, 0)
        + counts.get(STATUS_COMPLETE, 0)
    )
    analyzed_or_beyond = (
        counts.get(STATUS_ANALYZED, 0)
        + counts.get(STATUS_EVALUATING, 0)
        + counts.get(STATUS_EVALUATED, 0)
        + counts.get(STATUS_RECOMMENDING, 0)
        + counts.get(STATUS_COMPLETE, 0)
    )
    evaluated_or_beyond = (
        counts.get(STATUS_EVALUATED, 0)
        + counts.get(STATUS_RECOMMENDING, 0)
        + counts.get(STATUS_COMPLETE, 0)
    )
    evaluated_count = counts.get(STATUS_EVALUATED, 0)
    complete_count = counts.get(STATUS_COMPLETE, 0)

    def _rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100.0, 1)

    return DocumentSummaryResponse(
        queued_count=counts.get(STATUS_QUEUED, 0),
        extracting_count=counts.get(STATUS_EXTRACTING, 0),
        extracted_count=counts.get(STATUS_EXTRACTED, 0),
        analyzing_count=counts.get(STATUS_ANALYZING, 0),
        analyzed_count=counts.get(STATUS_ANALYZED, 0),
        evaluating_count=counts.get(STATUS_EVALUATING, 0),
        evaluated_count=evaluated_count,
        recommending_count=counts.get(STATUS_RECOMMENDING, 0),
        complete_count=complete_count,
        failed_count=counts.get(STATUS_FAILED, 0),
        total_count=total_count,
        agent1_success_rate=_rate(extracted_or_beyond, total_count),
        agent2_success_rate=_rate(analyzed_or_beyond, total_count),
        agent3_success_rate=_rate(evaluated_or_beyond, total_count),
        agent4_success_rate=_rate(complete_count, total_count),
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentDetailResponse:
    """Get document metadata and current extraction progress/status."""
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})
    return DocumentDetailResponse.model_validate(document)


@router.get("/{document_id}/extraction", response_model=ExtractionResponse)
def get_document_extraction(document_id: int, db: Session = Depends(get_db)) -> ExtractionResponse:
    """Get the latest persisted extraction payload for a document."""
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})

    extraction = (
        db.query(Extraction)
        .filter(Extraction.document_id == document_id)
        .order_by(Extraction.id.desc())
        .first()
    )
    if not extraction:
        return ExtractionResponse(document_id=document_id, extraction=None, message=document.progress_message or "No extraction yet")

    return ExtractionResponse(document_id=document_id, extraction=_serialize_extraction(document, extraction))


@router.post("/{document_id}/retry", response_model=RetryDocumentResponse)
def retry_document_extraction(document_id: int, db: Session = Depends(get_db)) -> RetryDocumentResponse:
    """Retry a failed extraction by resetting progress and re-enqueuing the task."""
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})
    if document.status != STATUS_FAILED:
        raise HTTPException(
            status_code=409,
            detail={"code": "invalid_retry_state", "message": "Only failed documents can be retried"},
        )

    progress = DocumentProgressService(db)
    progress.queued(document_id, "Retry requested. Task queued for extraction")
    document = db.get(Document, document_id)
    task_id = enqueue_extraction(document_id)
    if task_id and document is not None:
        document.task_id = task_id
        db.commit()
        db.refresh(document)

    if document is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})

    return RetryDocumentResponse(
        id=document.id,
        status=document.status,
        progress_percent=document.progress_percent,
        progress_stage=document.progress_stage,
        progress_message=document.progress_message,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a document, its extractions, and the stored file.

    For safety, we prevent deletion while a document is actively processing.
    """
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Document not found"},
        )
    if document.status in {
        STATUS_QUEUED,
        STATUS_EXTRACTING,
        STATUS_ANALYZING,
        STATUS_EVALUATING,
        STATUS_RECOMMENDING,
    }:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "cannot_delete_in_progress",
                "message": "Cannot delete a document while processing is in progress.",
            },
        )

    # Delete extractions first to keep FK constraints happy.
    db.query(Extraction).filter(Extraction.document_id == document_id).delete()
    db.delete(document)
    db.commit()

    # Best-effort delete of the physical file (does not affect API result).
    if document.file_path:
        delete_stored_file(document.file_path)
