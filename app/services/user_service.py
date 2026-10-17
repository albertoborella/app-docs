"""User provisioning domain rules: list, admin create/edit, deactivate/reactivate."""

from sqlmodel import Session, select

from app.core.security import hash_password, utc_now
from app.db.models import Role, User


class DuplicateUsernameError(ValueError):
    pass


def list_users(db: Session) -> list[User]:
    return list(db.exec(select(User).order_by(User.id)).all())


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, *, username: str, password: str, role: Role) -> User:
    existing = db.exec(select(User).where(User.username == username)).first()
    if existing is not None:
        raise DuplicateUsernameError(username)
    now = utc_now()
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    *,
    username: str | None = None,
    password: str | None = None,
    role: Role | None = None,
    is_active: bool | None = None,
) -> User:
    if username is not None:
        user.username = username
    if password is not None:
        user.password_hash = hash_password(password)
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    user.updated_at = utc_now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
