"""Integration tests for the documents API: CRUD, search/filter, soft delete & restore."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

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


def create_document(title, issuing_body, **fields):
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        now = utc_now()
        doc = Document(
            title=title, issuing_body=issuing_body, created_at=now, updated_at=now, **fields
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


def document_count():
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        return len(session.exec(select(Document)).all())


@pytest.fixture
def admin_token(client):
    create_user("admin", "adm1n-pass", role=Role.admin)
    return login_token(client, "admin", "adm1n-pass")


@pytest.fixture
def user_token(client):
    create_user("ana", "usr-pass", role=Role.user)
    return login_token(client, "ana", "usr-pass")


def create_via_api(client, token, **payload):
    return client.post("/api/v1/documents", headers=bearer(token), json=payload)


# --- Authentication & role gates -------------------------------------------------


def test_documents_list_requires_authentication(client):
    assert client.get("/api/v1/documents").status_code == 401


def test_admin_creates_document_with_201(client, admin_token):
    response = create_via_api(
        client,
        admin_token,
        title="Resolución 123",
        issuing_body="SENASA",
        description="Lácteos",
        document_type="resolución",
        issued_on="2024-05-01",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Resolución 123"
    assert body["issuing_body"] == "SENASA"
    assert body["description"] == "Lácteos"
    assert body["document_type"] == "resolución"
    assert body["issued_on"] == "2024-05-01"
    assert body["deleted_at"] is None


def test_arbitrary_free_text_issuing_body_is_stored_verbatim(client, admin_token):
    response = create_via_api(
        client, admin_token, title="Doc", issuing_body="Ministerio de Ganadería (MVD) — Región Este"
    )
    assert response.status_code == 201
    assert response.json()["issuing_body"] == "Ministerio de Ganadería (MVD) — Región Este"


def test_normal_user_cannot_create_document(client, user_token):
    before = document_count()
    response = create_via_api(client, user_token, title="Intruso", issuing_body="SENASA")
    assert response.status_code == 403
    assert response.json()["detail"] == "Se requiere rol de administrador."
    assert document_count() == before


def test_normal_user_cannot_update_document(client, admin_token, user_token):
    create_via_api(client, admin_token, title="Original", issuing_body="SENASA")
    response = client.patch(
        "/api/v1/documents/1", headers=bearer(user_token), json={"title": "Hack"}
    )
    assert response.status_code == 403


def test_normal_user_cannot_delete_document(client, admin_token, user_token):
    create_via_api(client, admin_token, title="Original", issuing_body="SENASA")
    response = client.delete("/api/v1/documents/1", headers=bearer(user_token))
    assert response.status_code == 403


# --- Catalog listing, search, filters --------------------------------------------


def test_normal_user_sees_whole_active_catalog(client, admin_token, user_token):
    create_via_api(client, admin_token, title="A", issuing_body="SENASA")
    create_via_api(client, admin_token, title="B", issuing_body="MVD")
    response = client.get("/api/v1/documents", headers=bearer(user_token))
    assert response.status_code == 200
    assert {item["title"] for item in response.json()} == {"A", "B"}


def test_query_search_matches_title_and_issuing_body(client, admin_token, user_token):
    create_via_api(client, admin_token, title="Resolución 123", issuing_body="SENASA")
    create_via_api(client, admin_token, title="Decreto 9", issuing_body="MVD")
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"query": "resoluci"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Resolución 123"]
    response = client.get("/api/v1/documents", headers=bearer(user_token), params={"query": "mvd"})
    assert [item["issuing_body"] for item in response.json()] == ["MVD"]


def test_no_match_search_returns_empty_without_error(client, admin_token, user_token):
    create_via_api(client, admin_token, title="A", issuing_body="SENASA")
    response = client.get("/api/v1/documents", headers=bearer(user_token), params={"query": "zzz"})
    assert response.status_code == 200
    assert response.json() == []


def test_filter_by_document_type_uses_contains(client, admin_token, user_token):
    create_via_api(
        client, admin_token, title="A", issuing_body="SENASA", document_type="Circular 2761"
    )
    create_via_api(
        client, admin_token, title="B", issuing_body="SENASA", document_type="Circular 2762"
    )
    create_via_api(
        client, admin_token, title="C", issuing_body="SENASA", document_type="Resolución"
    )
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"document_type": "2761"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["A"]
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"document_type": "circular"}
    )
    assert [item["title"] for item in response.json()] == ["A", "B"]


def test_filter_by_issuing_body_uses_contains(client, admin_token, user_token):
    create_via_api(client, admin_token, title="R", issuing_body="SENASA")
    create_via_api(client, admin_token, title="D", issuing_body="MVD")
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"issuing_body": "MV"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["D"]


def test_create_document_with_country_and_topic_round_trip(client, admin_token, user_token):
    response = create_via_api(
        client,
        admin_token,
        title="Circular 2761 B",
        issuing_body="MVD",
        country="Uruguay",
        topic="lácteos",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["country"] == "Uruguay"
    assert body["topic"] == "lácteos"

    listed = client.get("/api/v1/documents", headers=bearer(user_token))
    assert listed.status_code == 200
    item = listed.json()[0]
    assert item["country"] == "Uruguay"
    assert item["topic"] == "lácteos"


def test_country_and_topic_default_to_none(client, admin_token, user_token):
    create_via_api(client, admin_token, title="A", issuing_body="SENASA")
    response = client.get("/api/v1/documents", headers=bearer(user_token))
    assert response.status_code == 200
    item = response.json()[0]
    assert item["country"] is None
    assert item["topic"] is None


def test_filter_by_country_uses_contains(client, admin_token, user_token):
    create_via_api(client, admin_token, title="Uy", issuing_body="MVD", country="Uruguay")
    create_via_api(client, admin_token, title="Ar", issuing_body="MAGAP", country="Argentina")
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"country": "urugu"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Uy"]


def test_filter_by_topic_uses_contains(client, admin_token, user_token):
    create_via_api(
        client, admin_token, title="A", issuing_body="SENASA", topic="Produccion primaria"
    )
    create_via_api(client, admin_token, title="B", issuing_body="SENASA", topic="Comercio")
    create_via_api(client, admin_token, title="C", issuing_body="SENASA")  # topic NULL
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"topic": "primaria"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["A"]


def test_country_and_topic_filters_combine_with_query(client, admin_token, user_token):
    create_via_api(
        client,
        admin_token,
        title="Circular 1",
        issuing_body="MVD",
        country="Uruguay",
        topic="Produccion primaria",
    )
    create_via_api(
        client,
        admin_token,
        title="Circular 2",
        issuing_body="MVD",
        country="Uruguay",
        topic="Comercio",
    )
    create_via_api(
        client,
        admin_token,
        title="Circular 3",
        issuing_body="MVD",
        country="Chile",
        topic="Produccion primaria",
    )
    response = client.get(
        "/api/v1/documents",
        headers=bearer(user_token),
        params={"query": "circular", "country": "urugu", "topic": "primaria"},
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Circular 1"]


def test_admin_can_patch_country_and_topic(client, admin_token):
    create_via_api(client, admin_token, title="A", issuing_body="SENASA")
    response = client.patch(
        "/api/v1/documents/1",
        headers=bearer(admin_token),
        json={"country": "Uruguay", "topic": "lácteos"},
    )
    assert response.status_code == 200
    assert response.json()["country"] == "Uruguay"
    assert response.json()["topic"] == "lácteos"


# --- Soft delete, admin bin, restore ---------------------------------------------


def test_admin_delete_soft_deletes_and_record_remains(client, admin_token):
    create_via_api(client, admin_token, title="A", issuing_body="SENASA")
    response = client.delete("/api/v1/documents/1", headers=bearer(admin_token))
    assert response.status_code == 204
    assert document_count() == 1  # soft delete: row stays
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        doc = session.exec(select(Document).where(Document.id == 1)).one()
        assert doc.deleted_at is not None


def test_deleted_hidden_from_normal_users_in_list_and_search(client, admin_token, user_token):
    create_via_api(client, admin_token, title="Activo", issuing_body="SENASA")
    create_via_api(client, admin_token, title="Obsoleto", issuing_body="SENASA")
    client.delete("/api/v1/documents/2", headers=bearer(admin_token))
    response = client.get("/api/v1/documents", headers=bearer(user_token))
    assert [item["title"] for item in response.json()] == ["Activo"]
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"query": "obsoleto"}
    )
    assert response.json() == []


def test_admin_bin_lists_only_deleted(client, admin_token, user_token):
    create_via_api(client, admin_token, title="Activo", issuing_body="SENASA")
    create_via_api(client, admin_token, title="Obsoleto", issuing_body="SENASA")
    client.delete("/api/v1/documents/2", headers=bearer(admin_token))
    response = client.get(
        "/api/v1/documents", headers=bearer(admin_token), params={"deleted": "true"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Obsoleto"]
    assert response.json()[0]["deleted_at"] is not None


def test_normal_user_deleted_flag_is_ignored(client, admin_token, user_token):
    create_via_api(client, admin_token, title="Activo", issuing_body="SENASA")
    create_via_api(client, admin_token, title="Obsoleto", issuing_body="SENASA")
    client.delete("/api/v1/documents/2", headers=bearer(admin_token))
    response = client.get(
        "/api/v1/documents", headers=bearer(user_token), params={"deleted": "true"}
    )
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Activo"]  # bin never exposed


def test_admin_restores_document_and_it_reappears(client, admin_token, user_token):
    create_via_api(client, admin_token, title="A", issuing_body="SENASA")
    client.delete("/api/v1/documents/1", headers=bearer(admin_token))
    response = client.post("/api/v1/documents/1/restore", headers=bearer(admin_token))
    assert response.status_code == 200
    assert response.json()["deleted_at"] is None
    response = client.get("/api/v1/documents", headers=bearer(user_token))
    assert [item["title"] for item in response.json()] == ["A"]


def test_normal_user_cannot_restore(client, admin_token, user_token):
    create_via_api(client, admin_token, title="A", issuing_body="SENASA")
    client.delete("/api/v1/documents/1", headers=bearer(admin_token))
    response = client.post("/api/v1/documents/1/restore", headers=bearer(user_token))
    assert response.status_code == 403


# --- Admin updates & 404s ---------------------------------------------------------


def test_admin_updates_document_fields(client, admin_token):
    create_via_api(client, admin_token, title="Original", issuing_body="SENASA")
    response = client.patch(
        "/api/v1/documents/1", headers=bearer(admin_token), json={"title": "Actualizado"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Actualizado"
    assert response.json()["issuing_body"] == "SENASA"


def test_patch_unknown_document_returns_404(client, admin_token):
    response = client.patch(
        "/api/v1/documents/999", headers=bearer(admin_token), json={"title": "X"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Documento no encontrado."


def test_delete_unknown_document_returns_404(client, admin_token):
    response = client.delete("/api/v1/documents/999", headers=bearer(admin_token))
    assert response.status_code == 404


def test_restore_unknown_document_returns_404(client, admin_token):
    response = client.post("/api/v1/documents/999/restore", headers=bearer(admin_token))
    assert response.status_code == 404
