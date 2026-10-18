from datetime import date, datetime
from enum import Enum

from sqlalchemy import text
from sqlmodel import Field, Index, SQLModel


class Role(str, Enum):
    admin = "admin"
    user = "user"


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    role: Role
    is_active: bool = Field(default=True, index=True)
    created_at: datetime
    updated_at: datetime


class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"
    id: int = Field(primary_key=True)
    token_hash: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime
    expires_at: datetime = Field(index=True)


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_deleted_at_active", "deleted_at",
              sqlite_where=text("deleted_at IS NULL")),
    )
    id: int = Field(primary_key=True)
    title: str = Field(index=True)
    issuing_body: str = Field(index=True)
    description: str | None = None
    document_type: str | None = None
    country: str | None = Field(default=None, index=True)
    topic: str | None = Field(default=None, index=True)
    issued_on: date | None = None
    deleted_at: datetime | None = Field(default=None, index=True)
    created_at: datetime
    updated_at: datetime


class DocumentFile(SQLModel, table=True):
    __tablename__ = "document_files"
    id: int = Field(primary_key=True)
    document_id: int = Field(foreign_key="documents.id", unique=True, index=True)
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str = Field(index=True)
    stored_path: str
    uploaded_at: datetime
