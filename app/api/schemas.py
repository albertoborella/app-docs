"""Shared API request/response schemas (PEP 604 only)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import Role


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Role
    is_active: bool


class TokenResponse(BaseModel):
    token: str
    user: UserOut


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    role: Role


class UserPatch(BaseModel):
    username: str | None = Field(default=None, min_length=1)
    password: str | None = Field(default=None, min_length=1)
    role: Role | None = None
    is_active: bool | None = None


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1)
    issuing_body: str = Field(min_length=1)
    description: str | None = None
    document_type: str | None = None
    issued_on: date | None = None


class DocumentPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    issuing_body: str | None = Field(default=None, min_length=1)
    description: str | None = None
    document_type: str | None = None
    issued_on: date | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    issuing_body: str
    description: str | None
    document_type: str | None
    issued_on: date | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_at: datetime
