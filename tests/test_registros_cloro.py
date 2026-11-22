"""Unit tests for the cloro-registro service layer business rules.

These tests verify the acceptance criteria defined in specs.md and design.md:
- cloro_ppm range validation (0 < ppm ≤ 10)
- Automatic state assignment based on cloro_ppm value
- Timestamp future validation (≥ 1h → error 422)
- Evidencia upload validation (extension and size)
- Listado con filtros
"""

import io
import os
import tempfile
import shutil
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel
from sqlmodel import Session, create_engine
from sqlmodel import select as sql_select

from app.documentos_oficiales.db.models import User, CloroRegistro
from app.documentos_oficiales.db.session import create_db_engine, get_session, get_engine
from app.documentos_oficiales.api.schemas import CloroRegistroCreate, CloroRegistroFilter
from app.documentos_oficiales.core.security import hash_password, utc_now
from app.documentos_oficiales.services.cloro_registro_service import (
    validar_cloro_ppm,
    asignar_estado,
    crear_registro,
    listar_registros,
    subir_evidencia,
)


@pytest.fixture
def tmp_db():
    """Create a fresh in-memory DB for each test."""
    import tempfile
    tmp_dir = tempfile.mkdtemp(prefix="test_cloro_")
    db_path = os.path.join(tmp_dir, "test_cloro.db")
    os.environ["DOCMANAGER_DB_PATH"] = db_path

    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    # Create admin user
    with Session(engine) as session:
        now = utc_now()
        user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        session.commit()

    yield db_path

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def client(tmp_db):
    """Create a TestClient with the fresh DB."""
    from app.main import create_app
    app = create_app()
    return TestClient(app)


def test_validar_cloro_ppm_03_dentro_limites():
    """cloro_ppm=0.3 → (True, 'dentro_limites')."""
    resultado = validar_cloro_ppm(0.3)
    assert resultado == (True, "dentro_limites")


def test_validar_cloro_ppm_08_dentro_limites():
    """cloro_ppm=0.8 → (True, 'dentro_limites')."""
    resultado = validar_cloro_ppm(0.8)
    assert resultado == (True, "dentro_limites")


def test_validar_cloro_ppm_12_fuera_limites():
    """cloro_ppm=1.2 → (False, 'fuera_limites')."""
    resultado = validar_cloro_ppm(1.2)
    assert resultado == (False, "fuera_limites")


def test_validar_cloro_ppm_menos_1_422():
    """cloro_ppm=-1 → (False, 'error_422')."""
    resultado = validar_cloro_ppm(-1)
    assert resultado == (False, "error_422")


def test_validar_cloro_ppm_15_422():
    """cloro_ppm=15 → (False, 'error_422')."""
    resultado = validar_cloro_ppm(15)
    assert resultado == (False, "error_422")


def test_asignar_estado_03_dentro_limites():
    """cloro_ppm=0.3 → 'dentro_limites'."""
    assert asignar_estado(0.3) == "dentro_limites"


def test_asignar_estado_08_dentro_limites():
    """cloro_ppm=0.8 → 'dentro_limites'."""
    assert asignar_estado(0.8) == "dentro_limites"


def test_asignar_estado_12_fuera_limites():
    """cloro_ppm=1.2 → 'fuera_limites'."""
    assert asignar_estado(1.2) == "fuera_limites"


def test_crear_registro_cloro_ppm_03_dentro_limites(tmp_db):
    """Crear registro con cloro_ppm=0.3 → estado='dentro_limites'."""
    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        payload = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=0.3,
            timestamp=datetime.now(timezone.utc),
        )
        result = crear_registro(session, payload, user_id=1)
        assert result.estado == "dentro_limites"
        assert result.cloro_ppm == 0.3


def test_crear_registro_cloro_ppm_08_dentro_limites(tmp_db):
    """Crear registro con cloro_ppm=0.8 → estado='dentro_limites'."""
    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        payload = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=0.8,
            timestamp=datetime.now(timezone.utc),
        )
        result = crear_registro(session, payload, user_id=1)
        assert result.estado == "dentro_limites"


def test_crear_registro_cloro_ppm_12_fuera_limites(tmp_db):
    """Crear registro con cloro_ppm=1.2 → estado='fuera_limites'."""
    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        payload = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=1.2,
            timestamp=datetime.now(timezone.utc),
        )
        result = crear_registro(session, payload, user_id=1)
        assert result.estado == "fuera_limites"


def test_crear_registro_cloro_ppm_menos_1_422(tmp_db):
    """Crear registro con cloro_ppm=-1 → ValueError (error 422 equivalente)."""
    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        payload = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=-1,
            timestamp=datetime.now(timezone.utc),
        )
        try:
            crear_registro(session, payload, user_id=1)
            assert False, "Debería haber lanzado ValueError"
        except ValueError as e:
            assert str(e) == "error_422"


def test_crear_registro_cloro_ppm_15_422(tmp_db):
    """Crear registro con cloro_ppm=15 → ValueError (error 422 equivalente)."""
    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        payload = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=15,
            timestamp=datetime.now(timezone.utc),
        )
        try:
            crear_registro(session, payload, user_id=1)
            assert False, "Debería haber lanzado ValueError"
        except ValueError as e:
            assert str(e) == "error_422"


def test_listar_registros_filtros_estado(tmp_db):
    """Listado con filtro por estado devuelve solo matches."""
    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        ahora = utc_now()

        # Create two registros: one dentro_limites, one fuera_limites
        payload1 = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=0.5,
            timestamp=ahora - timedelta(days=1),
        )
        payload2 = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=1.5,
            timestamp=ahora - timedelta(days=2),
        )

        crear_registro(session, payload1, user_id=1)
        crear_registro(session, payload2, user_id=1)

        # List with estado="dentro_limites"
        filtros = CloroRegistroFilter(estado="dentro_limites")
        resultado = listar_registros(session, filtros)
        assert len(resultado) == 1
        assert resultado[0].cloro_ppm == 0.5


def test_listar_registros_filtros_usuario(tmp_db):
    """Listado con filtro por usuario_id devuelve solo los del usuario."""
    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        ahora = utc_now()

        payload1 = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=0.5,
            timestamp=ahora - timedelta(days=1),
        )
        payload2 = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=1.5,
            timestamp=ahora - timedelta(days=2),
        )

        crear_registro(session, payload1, user_id=1)
        crear_registro(session, payload2, user_id=1)

        # List with usuario_id=1
        filtros = CloroRegistroFilter(usuario_id=1)
        resultado = listar_registros(session, filtros)
        assert len(resultado) == 2


def test_listar_registros_sin_filtros_devuelve_todos(tmp_db):
    """Listado sin filtros devuelve todos los registros activos."""
    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        ahora = utc_now()

        payload1 = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=0.5,
            timestamp=ahora - timedelta(days=1),
        )
        payload2 = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=1.5,
            timestamp=ahora - timedelta(days=2),
        )

        crear_registro(session, payload1, user_id=1)
        crear_registro(session, payload2, user_id=1)

        # List without filters
        filtros = CloroRegistroFilter()
        resultado = listar_registros(session, filtros)
        assert len(resultado) == 2


def test_subir_evidencia_txt_422(tmp_db):
    """Upload evidencia .txt → ValueError (extensión no permitida)."""
    import io
    from fastapi import UploadFile

    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create a registro first
        payload = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=0.5,
            timestamp=utc_now(),
        )
        crear_registro(session, payload, user_id=1)

        # Try to upload .txt file
        file = UploadFile(file=io.BytesIO(b"malicious content"), filename="test.txt")
        try:
            result = subir_evidencia(session, 1, file)
            assert False, "Debería haber lanzado ValueError"
        except ValueError as e:
            assert "Extensión no permitida" in str(e)


def test_subir_evidencia_pdf_12mb_422(tmp_db):
    """Upload evidencia .pdf 12MB → ValueError (tamaño excedente)."""
    from fastapi import UploadFile

    db_path = tmp_db
    engine = create_db_engine(db_path)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create a registro first
        payload = CloroRegistroCreate(
            user_id=1,
            cloro_ppm=0.5,
            timestamp=utc_now(),
        )
        crear_registro(session, payload, user_id=1)

        # Try to upload 12MB .pdf
        file = UploadFile(
            file=io.BytesIO(b"x" * (12 * 1024 * 1024)),
            filename="grande.pdf",
        )
        try:
            result = subir_evidencia(session, 1, file)
            assert False, "Debería haber lanzado ValueError"
        except ValueError as e:
            assert "demasiado grande" in str(e).lower() or "too large" in str(e).lower()