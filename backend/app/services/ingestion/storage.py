"""Local file storage helpers for uploaded documents."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import UPLOAD_DIR
from app.core.exceptions import StorageError


def generate_storage_name(original_name: str) -> str:
    extension = Path(original_name or "document").suffix.lower()
    return f"{uuid.uuid4().hex}{extension}"


def save_upload(file: UploadFile, contents: bytes) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / generate_storage_name(file.filename or "document")
    try:
        target.write_bytes(contents)
    except OSError as exc:
        raise StorageError(f"Cannot save file: {exc}") from exc
    return target.resolve()


def delete_stored_file(path: str) -> None:
  """Best-effort deletion of a stored upload file."""
  try:
      file_path = Path(path)
  except TypeError:
      return
  try:
      if file_path.is_file():
          file_path.unlink()
  except OSError:
      # Swallow errors: file removal failures shouldn't break API flows.
      return