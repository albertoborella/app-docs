"""User management routes: GET/POST /users, PATCH /users/{id} (admin only)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.deps import require_admin
from app.api.schemas import UserCreate, UserOut, UserPatch
from app.db.models import User
from app.db.session import get_session
from app.services import user_service

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserOut])
def list_users(
    _: User = Depends(require_admin), db: Session = Depends(get_session)
) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in user_service.list_users(db)]


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> UserOut:
    try:
        user = user_service.create_user(
            db, username=payload.username, password=payload.password, role=payload.role
        )
    except user_service.DuplicateUsernameError:
        raise HTTPException(status_code=409, detail="El nombre de usuario ya existe.") from None
    return UserOut.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(
    user_id: int,
    payload: UserPatch,
    _: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> UserOut:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    user = user_service.update_user(db, user, **updates)
    return UserOut.model_validate(user)
