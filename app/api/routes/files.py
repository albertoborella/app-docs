"""File routes: admin upload/replace (PUT), authenticated download (GET)."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.api.deps import require_admin
from app.api.schemas import FileOut
from app.db.models import Document, User
from app.db.session import get_session
from app.services import document_service, file_service

router = APIRouter(tags=["files"])

_CHUNK_SIZE = 1024 * 1024


def _load_document(db: Session, document_id: int) -> Document:
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    return document


@router.put("/documents/{document_id}/file", response_model=FileOut)
async def upload_file(
    document_id: int,
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> FileOut:
    _load_document(db, document_id)  # deleted documents: admin replace allowed (design)
    if not file_service.is_allowed_filename(file.filename or ""):
        raise HTTPException(status_code=415, detail="Tipo de archivo no permitido.")
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(_CHUNK_SIZE):
        total += len(chunk)
        if total > file_service.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413, detail="Archivo demasiado grande. El máximo es 25 MB."
            )
        chunks.append(chunk)
    record = file_service.store_file(
        db,
        document_id=document_id,
        original_filename=file.filename or "",
        content_type=file.content_type or "application/octet-stream",
        data=b"".join(chunks),
    )
    return FileOut.model_validate(record)
