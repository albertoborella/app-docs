"""Shared API request/response schemas (PEP 604 only)."""

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
