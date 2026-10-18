"""File routes: admin upload/replace (PUT), authenticated download (GET)."""

from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlmodel import Session

from app.api.deps import get_current_user, require_admin
from app.api.schemas import FileOut
from app.db.models import Document, Role, User
from app.db.session import get_session
from app.services import document_service, file_service

router = APIRouter(tags=["files"])

_CHUNK_SIZE = 1024 * 1024


def _load_document(db: Session, document_id: int) -> Document:
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    return document


def _content_disposition(filename: str) -> str:
    fallback = filename.encode("ascii", "ignore").decode().replace('"', "") or "file"
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename)}"


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


@router.get("/documents/{document_id}/file")
def download_file(
    document_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> Response:
    document = _load_document(db, document_id)
    if document.deleted_at is not None and user.role != Role.admin:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    record = file_service.get_file_record(db, document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    data = file_service.read_stored_file(record)
    if data is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return Response(
        content=data,
        media_type=record.content_type,
        headers={"Content-Disposition": _content_disposition(record.original_filename)},
    )
