"""Document catalog domain rules: list/search/filter, admin CRUD, soft delete, restore."""

from datetime import date

from sqlmodel import Session, select

from app.core.security import utc_now
from app.db.models import Document


def list_documents(
    db: Session,
    *,
    query: str | None = None,
    document_type: str | None = None,
    issuing_body: str | None = None,
    country: str | None = None,
    topic: str | None = None,
    deleted: bool = False,
) -> list[Document]:
    stmt = select(Document)
    if deleted:
        stmt = stmt.where(Document.deleted_at.is_not(None))
    else:
        stmt = stmt.where(Document.deleted_at.is_(None))
    if query:
        # Unified free-text search across every metadata field (user request).
        stmt = stmt.where(
            Document.title.contains(query)
            | Document.issuing_body.contains(query)
            | Document.document_type.contains(query)
            | Document.country.contains(query)
            | Document.topic.contains(query)
            | Document.description.contains(query)
        )
    if document_type is not None:
        stmt = stmt.where(Document.document_type.contains(document_type))
    if issuing_body is not None:
        stmt = stmt.where(Document.issuing_body.contains(issuing_body))
    if country is not None:
        stmt = stmt.where(Document.country.contains(country))
    if topic is not None:
        stmt = stmt.where(Document.topic.contains(topic))
    return list(db.exec(stmt.order_by(Document.id)).all())


def get_document(db: Session, document_id: int) -> Document | None:
    return db.get(Document, document_id)


def create_document(
    db: Session,
    *,
    title: str,
    issuing_body: str,
    description: str | None = None,
    document_type: str | None = None,
    country: str | None = None,
    topic: str | None = None,
    issued_on: date | None = None,
) -> Document:
    now = utc_now()
    document = Document(
        title=title,
        issuing_body=issuing_body,
        description=description,
        document_type=document_type,
        country=country,
        topic=topic,
        issued_on=issued_on,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def update_document(db: Session, document: Document, **updates: object) -> Document:
    for field, value in updates.items():
        setattr(document, field, value)
    document.updated_at = utc_now()
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def soft_delete_document(db: Session, document: Document) -> Document:
    document.deleted_at = utc_now()
    document.updated_at = utc_now()
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def restore_document(db: Session, document: Document) -> Document:
    document.deleted_at = None
    document.updated_at = utc_now()
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
