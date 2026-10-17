"""Session domain rules: authenticate, mint/resolve/delete opaque sessions."""

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import (
    create_session_token,
    hash_token,
    is_token_expired,
    utc_now,
    verify_password,
)
from app.db.models import User, UserSession


def authenticate(db: Session, *, username: str, password: str) -> User | None:
    user = db.exec(select(User).where(User.username == username)).first()
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: Session, user: User) -> str:
    token = create_session_token()
    now = utc_now()
    db.add(
        UserSession(
            token_hash=hash_token(token),
            user_id=user.id,
            created_at=now,
            expires_at=now + get_settings().session_ttl,
        )
    )
    db.commit()
    return token


def resolve_session(db: Session, token: str) -> User | None:
    row = db.exec(select(UserSession).where(UserSession.token_hash == hash_token(token))).first()
    if row is None or is_token_expired(row.expires_at):
        return None
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        return None
    return user


def logout(db: Session, token: str) -> bool:
    row = db.exec(select(UserSession).where(UserSession.token_hash == hash_token(token))).first()
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True
