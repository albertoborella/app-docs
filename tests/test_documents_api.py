"""Integration tests for the documents API: catalog list/search/filter, soft-delete visibility."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from app.core.config import get_settings
from app.core.security import hash_password, utc_now
from app.db.models import Document, Role, User
from app.db.session import create_db_engine
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCMANAGER_DB_PATH", str(tmp_path / "test.db"))
    engine = create_db_engine(get_settings().db_path)
    SQLModel.metadata.create_all(engine)
    with Session(engine):
        yield TestClient(app)


def create_user(username, password, role=Role.user):
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        now = utc_now()
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def create_document(title, issuing_body, *, deleted=False, **fields):
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        now = utc_now()
        doc = Document(
            title=title,
            issuing_body=issuing_body,
            deleted_at=utc_now() if deleted else None,
            created_at=now,
            updated_at=now,
            **fields,
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc


def login_token(client, username, password):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token(client):
    create_user("admin", "adm1n-pass", role=Role.admin)
    return login_token(client, "admin", "adm1n-pass")


@pytest.fixture
def user_token(client):
    create_user("ana", "usr-pass", role=Role.user)
    return login_token(client, "ana", "usr-pass")


def test_documents_list_requires_authentication(client):
    assert client.get("/api/v1/documents").status_code == 401


def test_normal_user_sees_whole_active_catalog(client, user_token):
    create_document("A", "SENASA")
    create_document("B", "MVD")
    response = client.get("/api/v1/documents", headers=bearer(user_token))
    assert response.status_code == 200
    assert {item["title"] for item in response.json()} == {"A", "B"}


def test_query_search_matches_title_and_issuing_body(client, user_token):
    create_document("Resolución 123", "SENASA")
    create_document("Decreto 9", "MVD")
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"query": "resoluci"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Resolución 123"]
    response = client.get("/api/v1/documents", headers=bearer(user_token), params={"query": "mvd"})
    assert [item["issuing_body"] for item in response.json()] == ["MVD"]


def test_no_match_search_returns_empty_without_error(client, user_token):
    create_document("A", "SENASA")
    response = client.get("/api/v1/documents", headers=bearer(user_token), params={"query": "zzz"})
    assert response.status_code == 200
    assert response.json() == []


def test_filter_by_document_type(client, user_token):
    create_document("R", "SENASA", document_type="resolución")
    create_document("D", "SENASA", document_type="decreto")
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"document_type": "decreto"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["D"]


def test_filter_by_issuing_body(client, user_token):
    create_document("R", "SENASA")
    create_document("D", "MVD")
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"issuing_body": "MVD"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["D"]


def test_deleted_hidden_from_normal_users_in_list_and_search(client, user_token):
    create_document("Activo", "SENASA")
    create_document("Obsoleto", "SENASA", deleted=True)
    response = client.get("/api/v1/documents", headers=bearer(user_token))
    assert [item["title"] for item in response.json()] == ["Activo"]
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"query": "obsoleto"}
    )
    assert response.json() == []


def test_admin_bin_lists_only_deleted(client, admin_token, user_token):
    create_document("Activo", "SENASA")
    create_document("Obsoleto", "SENASA", deleted=True)
    response = client.get(
        "/api/v1/documents", headers=bearer(admin_token), params={"deleted": "true"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Obsoleto"]
    assert response.json()[0]["deleted_at"] is not None


def test_normal_user_deleted_flag_is_ignored(client, user_token):
    create_document("Activo", "SENASA")
    create_document("Obsoleto", "SENASA", deleted=True)
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"deleted": "true"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Activo"]  # bin never exposed
