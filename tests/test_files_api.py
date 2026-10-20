"""Integration tests for the file storage API: admin upload/replace, authed download, hardening."""

import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from app.core.config import get_settings
from app.core.security import hash_password, utc_now
from app.db.models import Document, DocumentFile, Role, User
from app.db.session import create_db_engine
from app.main import app

PDF_BYTES = b"%PDF-1.4 fake binary content \x00\x01\x02"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCMANAGER_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DOCMANAGER_STORAGE_DIR", str(tmp_path / "storage"))
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


def create_document(title, issuing_body):
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        now = utc_now()
        doc = Document(title=title, issuing_body=issuing_body, created_at=now, updated_at=now)
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc


def login_token(client, username, password):
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def upload_file(client, token, document_id, filename, content, content_type="application/pdf"):
    return client.put(
        f"/api/v1/documents/{document_id}/file",
        headers=bearer(token),
        files={"file": (filename, content, content_type)},
    )


def file_record(document_id):
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        return session.exec(
            select(DocumentFile).where(DocumentFile.document_id == document_id)
        ).first()


def file_record_count():
    engine = create_db_engine(get_settings().db_path)
    with Session(engine) as session:
        return len(session.exec(select(DocumentFile)).all())


def stored_file_path(document_id):
    return get_settings().storage_dir / "documents" / str(document_id) / "file"


@pytest.fixture
def admin_token(client):
    create_user("admin", "adm1n-pass", role=Role.admin)
    return login_token(client, "admin", "adm1n-pass")


@pytest.fixture
def user_token(client):
    create_user("ana", "usr-pass", role=Role.user)
    return login_token(client, "ana", "usr-pass")


# --- Admin upload: binary storage, sha256, size ----------------------------------


def test_admin_put_stores_binary_with_sha256_and_size(client, admin_token):
    document = create_document("Acta 1", "SENASA")
    response = upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document.id
    assert body["original_filename"] == "acta.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["size_bytes"] == len(PDF_BYTES)
    assert body["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    stored = stored_file_path(document.id)
    assert stored.read_bytes() == PDF_BYTES
    record = file_record(document.id)
    assert record is not None
    assert record.sha256 == body["sha256"]
    assert record.size_bytes == len(PDF_BYTES)
    assert record.stored_path == f"documents/{document.id}/file"


def test_admin_put_replaces_existing_file_in_place(client, admin_token):
    document = create_document("Acta 2", "SENASA")
    upload_file(client, admin_token, document.id, "v1.pdf", PDF_BYTES)
    replacement = b"%PDF-1.4 replacement \xff"
    response = upload_file(client, admin_token, document.id, "v2.pdf", replacement)
    assert response.status_code == 200
    assert response.json()["sha256"] == hashlib.sha256(replacement).hexdigest()
    assert stored_file_path(document.id).read_bytes() == replacement
    assert file_record_count() == 1  # unique per document, upserted


def test_put_unknown_document_returns_404(client, admin_token):
    response = upload_file(client, admin_token, 999, "acta.pdf", PDF_BYTES)
    assert response.status_code == 404
    assert response.json()["detail"] == "Documento no encontrado."


# --- Role gates & anonymous -------------------------------------------------------


def test_normal_user_cannot_upload(client, admin_token, user_token):
    document = create_document("Acta 3", "SENASA")
    before = file_record_count()
    response = upload_file(client, user_token, document.id, "acta.pdf", PDF_BYTES)
    assert response.status_code == 403
    assert response.json()["detail"] == "Se requiere rol de administrador."
    assert file_record_count() == before
    assert not stored_file_path(document.id).exists()


def test_anonymous_cannot_upload(client):
    document = create_document("Acta 4", "SENASA")
    response = upload_file(client, None, document.id, "acta.pdf", PDF_BYTES)
    assert response.status_code == 401


# --- Hardening: 415, 413, path escape ----------------------------------------------


def test_disallowed_extension_returns_415(client, admin_token):
    document = create_document("Acta 5", "SENASA")
    response = upload_file(
        client, admin_token, document.id, "malware.exe", b"MZ\x90\x00", "application/octet-stream"
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Tipo de archivo no permitido."
    assert file_record(document.id) is None
    assert not stored_file_path(document.id).exists()


def test_oversize_upload_returns_413(client, admin_token):
    document = create_document("Acta 6", "SENASA")
    oversized = b"x" * (25 * 1024 * 1024 + 1)
    response = upload_file(client, admin_token, document.id, "grande.pdf", oversized)
    assert response.status_code == 413
    assert response.json()["detail"] == "Archivo demasiado grande. El máximo es 25 MB."
    assert file_record(document.id) is None
    assert not stored_file_path(document.id).exists()


def test_client_filename_never_touches_filesystem(client, admin_token, tmp_path):
    document = create_document("Acta 7", "SENASA")
    response = upload_file(client, admin_token, document.id, "../../evil.pdf", PDF_BYTES)
    assert response.status_code == 200
    # Server-generated path is the only write target
    assert stored_file_path(document.id).read_bytes() == PDF_BYTES
    record = file_record(document.id)
    assert record.stored_path == f"documents/{document.id}/file"
    assert record.original_filename == "../../evil.pdf"  # metadata only, never a path
    # Nothing escaped the storage root
    assert list(tmp_path.rglob("evil.pdf")) == []


# --- Download: authed GET, deleted-document authz ----------------------------------


def test_authenticated_normal_user_downloads_file(client, admin_token, user_token):
    document = create_document("Acta 8", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    response = client.get(
        f"/api/v1/documents/{document.id}/file", headers=bearer(user_token)
    )
    assert response.status_code == 200
    assert response.content == PDF_BYTES
    assert response.headers["content-type"].startswith("application/pdf")
    assert "attachment" in response.headers["content-disposition"]
    assert "acta.pdf" in response.headers["content-disposition"]


def test_anonymous_cannot_download(client, admin_token):
    document = create_document("Acta 9", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    assert client.get(f"/api/v1/documents/{document.id}/file").status_code == 401


def test_get_without_stored_file_returns_404(client, admin_token, user_token):
    document = create_document("Acta 10", "SENASA")
    response = client.get(
        f"/api/v1/documents/{document.id}/file", headers=bearer(user_token)
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Archivo no encontrado."


def test_get_unknown_document_returns_404(client, user_token):
    response = client.get("/api/v1/documents/999/file", headers=bearer(user_token))
    assert response.status_code == 404


def test_deleted_document_file_hidden_from_normal_user(client, admin_token, user_token):
    document = create_document("Obsoleto", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    assert client.delete(
        f"/api/v1/documents/{document.id}", headers=bearer(admin_token)
    ).status_code == 204
    response = client.get(
        f"/api/v1/documents/{document.id}/file", headers=bearer(user_token)
    )
    assert response.status_code == 404  # no existence leak
    assert response.json()["detail"] == "Documento no encontrado."


def test_admin_still_downloads_deleted_document_file(client, admin_token):
    document = create_document("Obsoleto 2", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    client.delete(f"/api/v1/documents/{document.id}", headers=bearer(admin_token))
    response = client.get(
        f"/api/v1/documents/{document.id}/file", headers=bearer(admin_token)
    )
    assert response.status_code == 200
    assert response.content == PDF_BYTES


# --- Query token & inline disposition (mobile web direct open) ----------------------


def test_query_token_allows_download_without_header(client, admin_token, user_token):
    document = create_document("Acta Q1", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    response = client.get(f"/api/v1/documents/{document.id}/file?token={user_token}")
    assert response.status_code == 200
    assert response.content == PDF_BYTES
    assert "attachment" in response.headers["content-disposition"]
    assert "acta.pdf" in response.headers["content-disposition"]


def test_inline_param_sends_inline_disposition(client, admin_token, user_token):
    document = create_document("Acta Q2", "SENASA")
    upload_file(client, admin_token, document.id, "informe.pdf", PDF_BYTES)
    response = client.get(
        f"/api/v1/documents/{document.id}/file",
        headers=bearer(user_token),
        params={"inline": "true"},
    )
    assert response.status_code == 200
    disposition = response.headers["content-disposition"]
    assert disposition.startswith("inline;")
    assert "informe.pdf" in disposition
    assert "filename*=UTF-8''" in disposition  # filename logic unchanged


def test_default_and_inline_false_keep_attachment(client, admin_token, user_token):
    document = create_document("Acta Q3", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    for params in (None, {"inline": "false"}):
        response = client.get(
            f"/api/v1/documents/{document.id}/file",
            headers=bearer(user_token),
            params=params,
        )
        assert response.headers["content-disposition"].startswith("attachment;"), params


def test_invalid_query_token_returns_401(client, admin_token):
    document = create_document("Acta Q4", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    response = client.get(f"/api/v1/documents/{document.id}/file?token=token-invalido")
    assert response.status_code == 401
    assert response.json()["detail"] == "No autenticado."


def test_empty_query_token_returns_401(client, admin_token):
    document = create_document("Acta Q5", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    assert client.get(f"/api/v1/documents/{document.id}/file?token=").status_code == 401


def test_query_token_deleted_document_hidden_from_normal_user(client, admin_token, user_token):
    document = create_document("Obsoleto Q", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    client.delete(f"/api/v1/documents/{document.id}", headers=bearer(admin_token))
    response = client.get(f"/api/v1/documents/{document.id}/file?token={user_token}")
    assert response.status_code == 404  # authz identical on the query-token path
    assert response.json()["detail"] == "Documento no encontrado."


def test_bearer_header_takes_precedence_over_query_token(client, admin_token, user_token):
    document = create_document("Acta Q6", "SENASA")
    upload_file(client, admin_token, document.id, "acta.pdf", PDF_BYTES)
    response = client.get(
        f"/api/v1/documents/{document.id}/file?token=token-invalido",
        headers=bearer(user_token),
    )
    assert response.status_code == 200  # valid header wins over garbage query token


def test_upload_ignores_query_token_stays_header_only(client, admin_token):
    document = create_document("Acta Q7", "SENASA")
    response = client.put(
        f"/api/v1/documents/{document.id}/file?token={admin_token}",
        files={"file": ("acta.pdf", PDF_BYTES, "application/pdf")},
    )
    assert response.status_code == 401  # query token is GET-download only
