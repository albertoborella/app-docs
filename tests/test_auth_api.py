"""Integration tests for the auth API: login, me, logout (task 2.1)."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from app.core.config import get_settings
from app.core.security import create_session_token, hash_password, hash_token, utc_now
from app.db.models import Role, User, UserSession
from app.db.session import create_db_engine
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCMANAGER_DB_PATH", str(tmp_path / "test.db"))
    engine = create_db_engine(get_settings().db_path)
    SQLModel.metadata.create_all(engine)
    with Session(engine):
        yield TestClient(app)


def create_user(username="admin", password="adm1n-pass", role=Role.admin, is_active=True):
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


def login(client, username, password):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_success_returns_token_and_user(client):
    create_user()
    response = login(client, "admin", "adm1n-pass")
    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"


def test_login_wrong_password_returns_spanish_401(client):
    create_user()
    response = login(client, "admin", "wrong-pass")
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas."


def test_login_unknown_user_returns_401(client):
    response = login(client, "nadie", "whatever")
    assert response.status_code == 401


def test_login_deactivated_returns_401(client):
    create_user(is_active=False)
    response = login(client, "admin", "adm1n-pass")
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas."


def test_me_without_token_returns_401(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "No autenticado."


def test_me_with_invalid_token_returns_401(client):
    response = client.get("/api/v1/auth/me", headers=bearer("token-falso"))
    assert response.status_code == 401


def test_me_returns_current_user(client):
    create_user()
    token = login(client, "admin", "adm1n-pass").json()["token"]
    response = client.get("/api/v1/auth/me", headers=bearer(token))
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"
    assert body["is_active"] is True


def test_only_token_hash_is_persisted(client):
    create_user()
    token = login(client, "admin", "adm1n-pass").json()["token"]
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        rows = session.exec(select(UserSession)).all()
    assert len(rows) == 1
    assert rows[0].token_hash == hash_token(token)
    assert token not in {rows[0].token_hash}


def test_expired_token_rejected(client):
    create_user()
    token = create_session_token()
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        user = session.exec(select(User)).one()
        session.add(
            UserSession(
                token_hash=hash_token(token),
                user_id=user.id,
                created_at=utc_now() - timedelta(hours=13),
                expires_at=utc_now() - timedelta(hours=1),
            )
        )
        session.commit()
    response = client.get("/api/v1/auth/me", headers=bearer(token))
    assert response.status_code == 401


def test_deactivated_user_inflight_session_rejected(client):
    create_user()
    token = login(client, "admin", "adm1n-pass").json()["token"]
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        user = session.exec(select(User)).one()
        user.is_active = False
        session.add(user)
        session.commit()
    response = client.get("/api/v1/auth/me", headers=bearer(token))
    assert response.status_code == 401


def test_logout_deletes_session_row(client):
    create_user()
    token = login(client, "admin", "adm1n-pass").json()["token"]
    response = client.post("/api/v1/auth/logout", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["detail"] == "Sesión cerrada correctamente."
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        assert session.exec(select(UserSession)).all() == []
    assert client.get("/api/v1/auth/me", headers=bearer(token)).status_code == 401


def test_logout_without_token_returns_401(client):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 401
