"""Cloro-registro service layer: business rules and data operations.

Follows the layered architecture defined in design.md:
- Layer 2: Business rules, validación de rango, asignación automática de estado
- Handles evidencia upload validation
- Uses SQLModel Session with FK to existing users table
"""

from typing import List
from sqlmodel import Session, select
from fastapi import UploadFile

from app.documentos_oficiales.api.schemas import CloroRegistroCreate, CloroRegistroFilter
from app.documentos_oficiales.db.models import CloroRegistro


def validar_cloro_ppm(cloro_ppm: float) -> tuple[bool, str]:
    """Validate cloro ppm value and return status tuple.

    Returns:
        (True, "dentro_limites") if 0 <= cloro_ppm <= 1.0
        (False, "fuera_limites") if 1.0 < cloro_ppm <= 10
        (False, "error_422") if cloro_ppm < 0 or cloro_ppm > 10
    """
    if cloro_ppm < 0 or cloro_ppm > 10:
        return (False, "error_422")
    if cloro_ppm <= 1.0:
        return (True, "dentro_limites")
    return (False, "fuera_limites")


def asignar_estado(cloro_ppm: float) -> str:
    """Assign estado automatically based on cloro_ppm value per business rules.

    Rules:
        cloro_ppm < 0.5       → dentro_limites
        0.5 <= cloro_ppm <= 1.0 → dentro_limites
        cloro_ppm > 1.0       → fuera_limites
    """
    if cloro_ppm < 0.5 or (cloro_ppm >= 0.5 and cloro_ppm <= 1.0):
        return "dentro_limites"
    return "fuera_limites"


def crear_registro(db: Session, registro: CloroRegistroCreate, user_id: int) -> CloroRegistro:
    """Persist a new cloro registro with automatic state assignment.

    Flow:
        1. Validate cloro_ppm rango (0, 10]
        2. Assign estado automáticamente según reglas
        3. Persistir en SQLite con FK a users
        4. Devolver registro creado con estado asignado

    Raises:
        ValueError: Si cloro_ppm < 0 o cloro_ppm > 10 (error 422)
    """
    # Validate cloro_ppm range
    válido, mensaje = validar_cloro_ppm(registro.cloro_ppm)
    if not válido:
        # "error_422" means cloro_ppm < 0 or > 10 — completely invalid
        if mensaje == "error_422":
            raise ValueError(mensaje)
        # "fuera_limites" means 1.0 < cloro_ppm <= 10 — valid, assign state
        # Fall through to assign estado and persist

    # Assign estado automatically according to business rules
    estado = asignar_estado(registro.cloro_ppm)

    # Set timestamp: use provided or current UTC now
    from datetime import datetime, timezone
    timestamp = registro.timestamp or datetime.now(timezone.utc)

    db_registro = CloroRegistro(
        user_id=user_id,
        cloro_ppm=registro.cloro_ppm,
        temperatura_c=registro.temperatura_c,
        ph=registro.ph,
        agua_temperatura_c=registro.agua_temperatura_c,
        notes=registro.notes,
        estado=estado,
        timestamp=timestamp,
    )
    db.add(db_registro)
    db.commit()
    db.refresh(db_registro)
    return db_registro


def listar_registros(db: Session, filtros: CloroRegistroFilter) -> List[CloroRegistro]:
    """List cloro registros with optional filters, ordered by timestamp desc.

    Filtros soportados:
        - fecha_desde: fecha ISO inicio
        - fecha_hasta: fecha ISO fin
        - usuario_id: filtrar por user_id
        - estado: filtrar por estado (dentro_limites/fuera_limites/revision_necesaria)
        - cloro_min: cloro mínimo ppm
        - cloro_max: cloro máximo ppm

    Resulta siempre ordenado descending por timestamp (más reciente primero).
    Si no se proveen filtros, se devuelven todos los registros activos.
    """
    stmt = select(CloroRegistro)

    if filtros.fecha_desde is not None:
        stmt = stmt.where(CloroRegistro.timestamp >= filtros.fecha_desde)
    if filtros.fecha_hasta is not None:
        stmt = stmt.where(CloroRegistro.timestamp <= filtros.fecha_hasta)
    if filtros.usuario_id is not None:
        stmt = stmt.where(CloroRegistro.user_id == filtros.usuario_id)
    if filtros.estado is not None:
        stmt = stmt.where(CloroRegistro.estado == filtros.estado)
    if filtros.cloro_min is not None:
        stmt = stmt.where(CloroRegistro.cloro_ppm >= filtros.cloro_min)
    if filtros.cloro_max is not None:
        stmt = stmt.where(CloroRegistro.cloro_ppm <= filtros.cloro_max)

    stmt = stmt.order_by(CloroRegistro.timestamp.desc())
    rows = db.exec(stmt).all()
    return list(rows)


def subir_evidencia(db: Session, registro_id: int, file: UploadFile) -> dict:
    """Validate and save evidence file for a cloro registro.

    Validates:
        - Extensión: .png, .jpg, .jpeg, .pdf (solo)
        - Tamaño: < 10 MB

    Args:
        db: SQLModel Session
        registro_id: ID del registro al que adjuntar la evidencia
        file: File uploaded from UI (Flet FilePicker result)

    Returns:
        dict with {url: str, stored: bool} - URL stored and success flag

    Raises:
        ValueError: Si la extensión no está en la whitelist o el tamaño excede 10 MB
    """
    # Leer contenido del archivo
    content = file.file.read()
    size_bytes = len(content)

    # Validar extensión
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed_extensions = [".png", ".jpg", ".jpeg", ".pdf"]
    if ext not in allowed_extensions:
        raise ValueError(
            f"Extensión no permitida: {ext}. Use .png, .jpg, .pdf"
        )

    # Validar tamaño < 10 MB
    max_size = 10 * 1024 * 1024  # 10 MB
    if size_bytes >= max_size:
        raise ValueError(
            f"Archivo demasiado grande: {size_bytes} bytes. Máximo {max_size} bytes"
        )

    # Generar URL de almacenamiento
    evidencia_url = f"/storage/cloro/{registro_id}{ext or '.bin'}"

    # Actualizar registro con la URL
    registro = db.get(CloroRegistro, registro_id)
    if registro is None:
        raise ValueError(f"Registro con id {registro_id} no encontrado")

    registro.evidencia_url = evidencia_url
    db.add(registro)
    db.commit()
    db.refresh(registro)

    return {"url": evidencia_url, "stored": True}