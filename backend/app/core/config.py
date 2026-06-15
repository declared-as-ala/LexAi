"""Application configuration for Agent 1 backend."""

from __future__ import annotations

import os
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/legaltech")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "uploads")).resolve()
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "50"))
API_TITLE = os.environ.get("API_TITLE", "Legal-Tech Compliance API")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "FRONTEND_ORIGINS",
        "http://localhost:4173,http://127.0.0.1:4173,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

# LLM configuration (Agent 4 — Groq API)
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3-70b-8192")
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "30"))
LLM_ENABLED = bool(LLM_API_KEY)

# Image MIME types (routed to OCR pipeline)
IMAGE_MIME_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "image/webp",
}
IMAGE_EXTENSIONS: set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tiff",
    ".tif",
    ".bmp",
    ".webp",
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/html",
    *IMAGE_MIME_TYPES,
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".html",
    ".htm",
    *IMAGE_EXTENSIONS,
}

STATUS_UPLOADED = "uploaded"
STATUS_QUEUED = "queued"
STATUS_EXTRACTING = "extracting"
STATUS_EXTRACTED = "extracted"
STATUS_ANALYZING = "analyzing"
STATUS_ANALYZED = "analyzed"
STATUS_FAILED = "failed"

STAGE_QUEUED = "queued"
STAGE_STARTING = "starting"
STAGE_SELECTING_PROVIDER = "selecting_provider"
STAGE_EXTRACTING = "extracting"
STAGE_NORMALIZING = "normalizing"
STAGE_PERSISTING = "persisting"
STAGE_COMPLETED = "completed"
STAGE_FAILED = "failed"

# Agent 2 stages
STAGE_ANALYZING = "analyzing"
STAGE_SEGMENTING = "segmenting"
STAGE_CLASSIFYING = "classifying"
STAGE_NLP_PERSISTING = "nlp_persisting"
STAGE_NLP_COMPLETED = "nlp_completed"

# Agent 3 statuses / stages
STATUS_EVALUATING = "evaluating"
STATUS_EVALUATED = "evaluated"
STAGE_EVALUATING = "evaluating"
STAGE_EVAL_RULES = "eval_rules"
STAGE_EVAL_SCORING = "eval_scoring"
STAGE_EVAL_PERSISTING = "eval_persisting"
STAGE_EVAL_COMPLETED = "eval_completed"

# Agent 4 statuses / stages
STATUS_RECOMMENDING = "recommending"
STATUS_COMPLETE = "complete"
STAGE_RECOMMENDING = "recommending"
STAGE_REC_TEMPLATES = "rec_templates"
STAGE_REC_LLM = "rec_llm"
STAGE_REC_PERSISTING = "rec_persisting"
STAGE_REC_COMPLETED = "rec_completed"

STAGE_PROGRESS_DEFAULTS = {
    STAGE_QUEUED: 5,
    STAGE_STARTING: 15,
    STAGE_SELECTING_PROVIDER: 25,
    STAGE_EXTRACTING: 35,
    STAGE_NORMALIZING: 75,
    STAGE_PERSISTING: 90,
    STAGE_COMPLETED: 100,
    STAGE_FAILED: 100,
    STAGE_ANALYZING: 0,
    STAGE_SEGMENTING: 20,
    STAGE_CLASSIFYING: 60,
    STAGE_NLP_PERSISTING: 90,
    STAGE_NLP_COMPLETED: 100,
    STAGE_EVALUATING: 0,
    STAGE_EVAL_RULES: 30,
    STAGE_EVAL_SCORING: 60,
    STAGE_EVAL_PERSISTING: 85,
    STAGE_EVAL_COMPLETED: 100,
    STAGE_RECOMMENDING: 0,
    STAGE_REC_TEMPLATES: 40,
    STAGE_REC_LLM: 58,
    STAGE_REC_PERSISTING: 85,
    STAGE_REC_COMPLETED: 100,
}