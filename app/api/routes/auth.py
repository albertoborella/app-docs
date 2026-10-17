"""Auth routes: POST /auth/login, POST /auth/logout, GET /auth/me."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session

from app.api.deps import bearer_scheme, get_current_user
from app.api.schemas import LoginRequest, TokenResponse, UserOut
from app.db.models import User
from app.db.session import get_session
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_session)) -> TokenResponse:
    user = auth_service.authenticate(db, username=payload.username, password=payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    token = auth_service.create_session(db, user)
    return TokenResponse(token=token, user=UserOut.model_validate(user))


@router.post("/auth/logout")
def logout(
    _: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_session),
) -> dict[str, str]:
    auth_service.logout(db, credentials.credentials)
    return {"detail": "Sesión cerrada correctamente."}


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
