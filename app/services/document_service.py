"""Document catalog domain rules: list/search/filter, admin CRUD, soft delete, restore."""

import re
import unicodedata
from datetime import date

from sqlmodel import Session, select

from app.core.security import utc_now
from app.db.models import Document

_ALPHANUM_SPLIT = re.compile(r"(\d+)")


def _title_sort_key(document: Document) -> tuple[tuple[int, int, str], ...]:
    """Alphanumeric catalog order: case- and accent-insensitive, natural numbers.

    "Ácido" and "árbol" sort next to "A"/"a" (SQLite's NOCASE would push them
    after "Z"), and "Doc 2" precedes "Doc 10".
    """
    decomposed = unicodedata.normalize("NFD", document.title or "")
    folded = "".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold()
    parts = (part for part in _ALPHANUM_SPLIT.split(folded) if part)
    # Every element is (is_number, number, text) so comparisons stay type-safe.
    return tuple(
        (1, int(part), "") if part.isdigit() else (0, 0, part) for part in parts
    )


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
    documents = list(db.exec(stmt.order_by(Document.id)).all())
    # Stable sort over the id-ordered rows: ties keep their insertion order.
    documents.sort(key=_title_sort_key)
    return documents


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
