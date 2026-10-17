"""Integration tests for the users API: admin provisioning, roles, deactivation."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from app.core.config import get_settings
from app.core.security import hash_password, utc_now
from app.db.models import Role, User
from app.db.session import create_db_engine
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCMANAGER_DB_PATH", str(tmp_path / "test.db"))
    engine = create_db_engine(get_settings().db_path)
    SQLModel.metadata.create_all(engine)
    with Session(engine):
        yield TestClient(app)


def create_user(username, password, role=Role.user, is_active=True):
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        now = utc_now()
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def login_token(client, username, password):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def user_count():
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        return len(session.exec(select(User)).all())


@pytest.fixture
def admin_token(client):
    create_user("admin", "adm1n-pass", role=Role.admin)
    return login_token(client, "admin", "adm1n-pass")


@pytest.fixture
def user_token(client):
    create_user("ana", "usr-pass", role=Role.user)
    return login_token(client, "ana", "usr-pass")


def test_users_list_requires_authentication(client):
    assert client.get("/api/v1/users").status_code == 401


def test_normal_user_cannot_list_users(client, user_token):
    response = client.get("/api/v1/users", headers=bearer(user_token))
    assert response.status_code == 403
    assert response.json()["detail"] == "Se requiere rol de administrador."


def test_admin_lists_users_without_password_hash(client, admin_token):
    create_user("ana", "usr-pass", role=Role.user)
    response = client.get("/api/v1/users", headers=bearer(admin_token))
    assert response.status_code == 200
    usernames = {item["username"] for item in response.json()}
    assert usernames == {"admin", "ana"}
    assert "password_hash" not in response.text


def test_admin_creates_user_and_holder_can_sign_in(client, admin_token):
    response = client.post(
        "/api/v1/users",
        headers=bearer(admin_token),
        json={"username": "luis", "password": "nueva-pass", "role": "user"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "luis"
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert login_token(client, "luis", "nueva-pass")


def test_admin_creates_admin_role(client, admin_token):
    response = client.post(
        "/api/v1/users",
        headers=bearer(admin_token),
        json={"username": "otro-admin", "password": "admin2-pass", "role": "admin"},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "admin"


def test_create_duplicate_username_returns_409(client, admin_token):
    response = client.post(
        "/api/v1/users",
        headers=bearer(admin_token),
        json={"username": "admin", "password": "x-pass", "role": "user"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "El nombre de usuario ya existe."


def test_create_with_invalid_role_returns_422(client, admin_token):
    response = client.post(
        "/api/v1/users",
        headers=bearer(admin_token),
        json={"username": "x", "password": "x-pass", "role": "superuser"},
    )
    assert response.status_code == 422


def test_normal_user_cannot_create_accounts(client, user_token):
    before = user_count()
    response = client.post(
        "/api/v1/users",
        headers=bearer(user_token),
        json={"username": "intruso", "password": "x-pass", "role": "admin"},
    )
    assert response.status_code == 403
    assert user_count() == before


def test_no_self_registration_path_exists(client):
    paths = client.get("/openapi.json").json()["paths"]
    forbidden = ("register", "signup", "sign-up", "sign_up")
    assert not any(token in path.lower() for path in paths for token in forbidden)
    assert (
        client.post(
            "/api/v1/users", json={"username": "anon", "password": "x", "role": "user"}
        ).status_code
        == 401
    )


def test_admin_deactivates_user_and_sign_in_fails(client, admin_token):
    create_user("luis", "usr-pass")
    response = client.patch(
        "/api/v1/users/2",
        headers=bearer(admin_token),
        json={"is_active": False},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert user_count() == 2  # record remains
    assert (
        client.post(
            "/api/v1/auth/login", json={"username": "luis", "password": "usr-pass"}
        ).status_code
        == 401
    )


def test_admin_reactivates_user_and_sign_in_works_again(client, admin_token):
    create_user("luis", "usr-pass", is_active=False)
    response = client.patch(
        "/api/v1/users/2",
        headers=bearer(admin_token),
        json={"is_active": True},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert login_token(client, "luis", "usr-pass")


def test_admin_edits_password_and_username(client, admin_token):
    create_user("luis", "usr-pass")
    response = client.patch(
        "/api/v1/users/2",
        headers=bearer(admin_token),
        json={"username": "luis-mod", "password": "rotada-pass"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "luis-mod"
    assert login_token(client, "luis-mod", "rotada-pass")


def test_admin_changes_role(client, admin_token):
    create_user("luis", "usr-pass")
    response = client.patch(
        "/api/v1/users/2",
        headers=bearer(admin_token),
        json={"role": "admin"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_patch_unknown_user_returns_404(client, admin_token):
    response = client.patch(
        "/api/v1/users/999",
        headers=bearer(admin_token),
        json={"is_active": False},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario no encontrado."


def test_normal_user_cannot_patch_accounts(client, user_token):
    create_user("admin", "adm1n-pass", role=Role.admin)
    response = client.patch(
        "/api/v1/users/2",
        headers=bearer(user_token),
        json={"is_active": False},
    )
    assert response.status_code == 403
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        assert session.exec(select(User).where(User.id == 2)).one().is_active is True
