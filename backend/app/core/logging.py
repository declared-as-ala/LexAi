"""Structured logger setup for backend services."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import LOG_LEVEL


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_DEF_HANDLER: logging.Handler | None = None


def configure_logging() -> None:
    global _DEF_HANDLER
    root = logging.getLogger()
    if _DEF_HANDLER is not None:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.setLevel(LOG_LEVEL.upper())
    root.handlers.clear()
    root.addHandler(handler)
    _DEF_HANDLER = handler


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)