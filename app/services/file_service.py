"""File storage domain rules: extension allowlist, size cap, server-generated paths, upsert."""

import hashlib
from pathlib import Path

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import utc_now
from app.db.models import DocumentFile

ALLOWED_EXTENSIONS = frozenset({".pdf", ".docx", ".xlsx", ".odt", ".png", ".jpg"})
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


class FileTypeNotAllowedError(Exception):
    """Uploaded filename extension is not in the allowlist."""


class FileTooLargeError(Exception):
    """Uploaded content exceeds the size cap."""


def is_allowed_filename(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def stored_file_path(document_id: int) -> Path:
    """Server-generated storage path; validated so it can never escape the storage root."""
    root = get_settings().storage_dir.resolve()
    path = (root / "documents" / str(document_id) / "file").resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"storage path escapes root: {path}")
    return path


def get_file_record(db: Session, document_id: int) -> DocumentFile | None:
    return db.exec(
        select(DocumentFile).where(DocumentFile.document_id == document_id)
    ).first()


def store_file(
    db: Session,
    *,
    document_id: int,
    original_filename: str,
    content_type: str,
    data: bytes,
) -> DocumentFile:
    if not is_allowed_filename(original_filename):
        raise FileTypeNotAllowedError(original_filename)
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(len(data))
    path = stored_file_path(document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    record = get_file_record(db, document_id)
    now = utc_now()
    if record is None:
        record = DocumentFile(
            document_id=document_id,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            stored_path=f"documents/{document_id}/file",
            uploaded_at=now,
        )
    else:
        record.original_filename = original_filename
        record.content_type = content_type
        record.size_bytes = len(data)
        record.sha256 = hashlib.sha256(data).hexdigest()
        record.uploaded_at = now
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
