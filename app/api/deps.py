"""FastAPI dependencies: bearer extraction, get_current_user, require_admin."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.db.models import Role, User
from app.db.session import get_session
from app.services import auth_service

bearer_scheme = HTTPBearer(auto_error=False)

_AUTH_401 = HTTPException(
    status_code=401, detail="No autenticado.", headers={"WWW-Authenticate": "Bearer"}
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise _AUTH_401
    user = auth_service.resolve_session(db, credentials.credentials)
    if user is None:
        raise _AUTH_401
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador.")
    return user
