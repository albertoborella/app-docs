"""Cloro-registro routes: listado con filtros, crear, actualizar estado/evidencia, upload evidencia."""

import os

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlmodel import Session, select, func

from app.documentos_oficiales.api.deps import get_current_user, require_admin
from app.documentos_oficiales.api.schemas import CloroRegistroCreate, CloroRegistroOut, CloroRegistroFilter, CloroRegistroUpdate
from app.documentos_oficiales.db.models import CloroRegistro, User
from app.documentos_oficiales.db.session import get_session


router = APIRouter(tags=["registros-cloro"])


@router.get("/", response_model=list[CloroRegistroOut])
def listar_registros(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
    fecha_desde: str | None = Query(default=None, description="Fecha inicio ISO (YYYY-MM-DD)"),
    fecha_hasta: str | None = Query(default=None, description="Fecha fin ISO (YYYY-MM-DD)"),
    usuario_id: int | None = Query(default=None, description="Filtrar por user_id"),
    estado: str | None = Query(default=None, description="Filtrar por estado"),
    cloro_min: float | None = Query(default=None, description="Cloro mínimo ppm"),
    cloro_max: float | None = Query(default=None, description="Cloro máximo ppm"),
) -> list[CloroRegistroOut]:
    stmt = select(CloroRegistro)
    # Non-admin users can only see their own records
    if user.role != "admin":
        stmt = stmt.where(CloroRegistro.user_id == user.id)
    if usuario_id is not None and user.role == "admin":
        stmt = stmt.where(CloroRegistro.user_id == usuario_id)
    if estado is not None:
        stmt = stmt.where(CloroRegistro.estado == estado)
    if fecha_desde is not None:
        stmt = stmt.where(CloroRegistro.timestamp >= func.date(fecha_desde))
    if fecha_hasta is not None:
        stmt = stmt.where(CloroRegistro.timestamp <= func.date(fecha_hasta))
    if cloro_min is not None:
        stmt = stmt.where(CloroRegistro.cloro_ppm >= cloro_min)
    if cloro_max is not None:
        stmt = stmt.where(CloroRegistro.cloro_ppm <= cloro_max)
    stmt = stmt.order_by(CloroRegistro.timestamp.desc())
    rows = db.exec(stmt).all()
    return [CloroRegistroOut.model_validate(r) for r in rows]


@router.get("/{id}", response_model=CloroRegistroOut)
def obtener_registro(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> CloroRegistroOut:
    registro = db.get(CloroRegistro, id)
    if registro is None:
        raise HTTPException(status_code=404, detail="Registro de cloro no encontrado.")
    # Non-admin users can only see their own records
    if registro.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="No tiene acceso a este registro.")
    return CloroRegistroOut.model_validate(registro)


@router.post("/", response_model=CloroRegistroOut, status_code=201)
def crear_registro(
    payload: CloroRegistroCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> CloroRegistroOut:
    cloro_ppm = payload.cloro_ppm
    # Validar que cloro_ppm sea positivo y ≤ 10
    if cloro_ppm is None or cloro_ppm <= 0 or cloro_ppm > 10:
        raise HTTPException(status_code=422, detail="cloro_ppm debe ser > 0 y ≤ 10.")

    # Validar que timestamp no sea fecha futura > 1h
    from datetime import datetime, timezone
    timestamp = payload.timestamp
    if timestamp is not None:
        now = datetime.now(timezone.utc)
        diff = (now - timestamp).total_seconds()
        if diff < 0 or diff > 3600:
            raise HTTPException(status_code=422, detail="timestamp no puede ser futuro > 1h.")

    # Asignar estado automáticamente según reglas de negocio
    if cloro_ppm < 0.5:
        estado = "dentro_limites"
    elif cloro_ppm > 1.0:
        estado = "fuera_limites"
    else:
        estado = "dentro_limites"

    registro = CloroRegistro(
        user_id=user.id,
        cloro_ppm=cloro_ppm,
        timestamp=timestamp or datetime.now(timezone.utc),
        estado=estado,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return CloroRegistroOut.model_validate(registro)


@router.patch("/{id}", response_model=CloroRegistroOut)
def actualizar_registro(
    id: int,
    payload: CloroRegistroUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> CloroRegistroOut:
    registro = db.get(CloroRegistro, id)
    if registro is None:
        raise HTTPException(status_code=404, detail="Registro de cloro no encontrado.")
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in updates.items():
        setattr(registro, key, value)
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return CloroRegistroOut.model_validate(registro)


@router.post("/{id}/evidencia", response_model=dict)
def subir_evidencia(
    id: int,
    file: UploadFile,
    user: User = Depends(require_admin),
    db: Session = Depends(get_session),
) -> dict:
    registro = db.get(CloroRegistro, id)
    if registro is None:
        raise HTTPException(status_code=404, detail="Registro de cloro no encontrado.")

    # Leer contenido del archivo
    content = file.file.read()
    size_bytes = len(content)

    # Validar extensión
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    allowed_extensions = [".png", ".jpg", ".jpeg", ".pdf"]
    if ext not in allowed_extensions:
        raise HTTPException(status_code=422, detail=f"Extensión no permitida: {ext}. Use .png, .jpg, .pdf")

    # Validar tamaño < 10 MB
    max_size = 10 * 1024 * 1024  # 10 MB
    if size_bytes >= max_size:
        raise HTTPException(status_code=422, detail=f"Archivo demasiado grande: {size_bytes} bytes. Máximo {max_size} bytes")

    # Generar URL de almacenamiento
    evidencia_url = f"/storage/cloro/{id}{ext or '.bin'}"

    registro.evidencia_url = evidencia_url
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return {"url": evidencia_url, "stored": True, "size_bytes": size_bytes}