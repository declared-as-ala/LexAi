"""Custom application exceptions and error payload helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    message: str
    status_code: int = 400
    code: str = "app_error"


class UnsupportedDocumentError(AppError):
    def __init__(self, message: str = "Unsupported document type") -> None:
        super().__init__(message=message, status_code=422, code="unsupported_document")


class StorageError(AppError):
    def __init__(self, message: str = "Could not persist uploaded file") -> None:
        super().__init__(message=message, status_code=500, code="storage_error")