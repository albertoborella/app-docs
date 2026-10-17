"""Document routes: list/search/filter; admin CRUD, soft delete, restore land next."""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_current_user
from app.api.schemas import DocumentOut
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
    deleted: bool = Query(default=False),
) -> list[DocumentOut]:
    documents = document_service.list_documents(
        db,
        query=query,
        document_type=document_type,
        issuing_body=issuing_body,
        deleted=deleted and user.role == Role.admin,
    )
    return [DocumentOut.model_validate(d) for d in documents]
