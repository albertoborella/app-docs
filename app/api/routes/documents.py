"""Document routes: list/search/filter, admin CRUD, soft delete, restore."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import get_current_user, require_admin
from app.api.schemas import DocumentCreate, DocumentOut, DocumentPatch
from app.db.models import Role, User
from app.db.session import get_session
from app.services import document_service

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    query: str | None = None,
    document_type: str | None = None,
    issuing_body: str | None = None,
    country: str | None = None,
    topic: str | None = None,
    deleted: bool = Query(default=False),
) -> list[DocumentOut]:
    documents = document_service.list_documents(
        db,
        query=query,
        document_type=document_type,
        issuing_body=issuing_body,
        country=country,
        topic=topic,
        deleted=deleted and user.role == Role.admin,
    )
    return [DocumentOut.model_validate(d) for d in documents]


@router.post("/documents", response_model=DocumentOut, status_code=201)
def create_document(
    payload: DocumentCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> DocumentOut:
    document = document_service.create_document(db, **payload.model_dump())
    return DocumentOut.model_validate(document)


@router.patch("/documents/{document_id}", response_model=DocumentOut)
def patch_document(
    document_id: int,
    payload: DocumentPatch,
    _: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> DocumentOut:
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    document = document_service.update_document(db, document, **updates)
    return DocumentOut.model_validate(document)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> None:
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    document_service.soft_delete_document(db, document)


@router.post("/documents/{document_id}/restore", response_model=DocumentOut)
def restore_document(
    document_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> DocumentOut:
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    document = document_service.restore_document(db, document)
    return DocumentOut.model_validate(document)
