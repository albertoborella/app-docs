"""Document catalog domain rules: list/search/filter, admin CRUD, soft delete, restore."""

from sqlmodel import Session, select

from app.db.models import Document


def list_documents(
    db: Session,
    *,
    query: str | None = None,
    document_type: str | None = None,
    issuing_body: str | None = None,
    deleted: bool = False,
) -> list[Document]:
    stmt = select(Document)
    if deleted:
        stmt = stmt.where(Document.deleted_at.is_not(None))
    else:
        stmt = stmt.where(Document.deleted_at.is_(None))
    if query:
        stmt = stmt.where(
            Document.title.contains(query) | Document.issuing_body.contains(query)
        )
    if document_type is not None:
        stmt = stmt.where(Document.document_type == document_type)
    if issuing_body is not None:
        stmt = stmt.where(Document.issuing_body == issuing_body)
    return list(db.exec(stmt.order_by(Document.id)).all())
