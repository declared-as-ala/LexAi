"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes import analysis, documents, evaluation, recommendation, rewrite
from app.api.routes.documents import process_contract_upload
from app.schemas.document import UploadDocumentResponse
from app.core.config import API_TITLE, FRONTEND_ORIGINS, LLM_ENABLED
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.db.migrate import run_startup_migrations
from app.db.session import SessionLocal
from app.services.ingestion.recovery import recover_interrupted_documents

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title=API_TITLE, version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(evaluation.router)
app.include_router(recommendation.router)
app.include_router(rewrite.router)


@app.post("/upload-contract", response_model=UploadDocumentResponse, status_code=201, tags=["documents"])
def upload_contract(file: UploadFile = File(...), db: Session = Depends(get_db)) -> UploadDocumentResponse:
    """Alias for contract upload (same behaviour as ``POST /documents/upload``)."""
    return process_contract_upload(file, db)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.on_event("startup")
def startup() -> None:
    run_startup_migrations()
    db = SessionLocal()
    try:
        recover_interrupted_documents(db)
    finally:
        db.close()


@app.get("/health")
def health():
    """Liveness + feature flags for the SPA (LLM Agent 4, image/OCR ingest)."""
    logger.info("health_check", extra={"extra": {"route": "/health"}})
    return {
        "status": "ok",
        "agent4_llm_enabled": LLM_ENABLED,
        "image_ocr_upload": True,
        "ocr_backend": "tesseract",
    }