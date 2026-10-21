"""Contract tests for the UI API client (task 5.1) — mocked httpx, no network."""

import json
from pathlib import Path

import httpx
import pytest

from app.db.models import Role
from app.ui.api_client import ApiClient, ApiError, AuthError, NotFoundError

BASE_URL = "http://testserver"


def make_client(handler, *, base_url: str = BASE_URL, token: str | None = None) -> ApiClient:
    return ApiClient(base_url=base_url, token=token, transport=httpx.MockTransport(handler))


def authorization_header(request: httpx.Request) -> str | None:
    return request.headers.get("Authorization")


def test_default_base_url_from_env(monkeypatch):
    monkeypatch.setenv("DOCMANAGER_API_URL", "http://env.example:9000")
    client = ApiClient()
    assert client.base_url == "http://env.example:9000"


def test_default_base_url_fallback():
    client = ApiClient(base_url=BASE_URL)
    assert client.base_url == BASE_URL


def test_login_success_stores_token_and_returns_user():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/auth/login"
        assert request.method == "POST"
        return httpx.Response(
            200,
            json={
                "token": "tok-abc",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "role": "admin",
                    "is_active": True,
                },
            },
        )

    client = make_client(handler)
    user = client.login("admin", "secret")

    assert client.token == "tok-abc"
    assert user.username == "admin"
    assert user.role == "admin"


def test_login_401_raises_auth_error_with_spanish_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Credenciales inválidas."})

    client = make_client(handler)
    with pytest.raises(AuthError) as exc_info:
        client.login("admin", "wrong")

    assert exc_info.value.status_code == 401
    assert "Credenciales inválidas." in str(exc_info.value)
    assert client.token is None


def test_bearer_header_sent_on_authenticated_request():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[])

    client = make_client(handler, token="tok-xyz")
    client.list_documents()

    assert authorization_header(seen[0]) == "Bearer tok-xyz"


def test_list_documents_serializes_filters_to_query_string():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[])

    client = make_client(handler, token="t")
    client.list_documents(
        query="resolución",
        document_type="Decreto",
        issuing_body="MAGAP",
        country="Uruguay",
        topic="lácteos",
        deleted=True,
    )

    url = seen[0].url
    assert url.path == "/api/v1/documents"
    assert url.params["query"] == "resolución"
    assert url.params["document_type"] == "Decreto"
    assert url.params["issuing_body"] == "MAGAP"
    assert url.params["country"] == "Uruguay"
    assert url.params["topic"] == "lácteos"
    assert url.params["deleted"] == "true"


def test_list_documents_omits_none_filters():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[])

    client = make_client(handler, token="t")
    client.list_documents()

    params = dict(seen[0].url.params)
    assert params == {}


def test_list_documents_returns_document_models():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "id": 7,
                    "title": "Resolución 001",
                    "issuing_body": "MAGAP",
                    "description": None,
                    "document_type": "Resolución",
                    "country": None,
                    "topic": None,
                    "issued_on": "2024-01-15",
                    "deleted_at": None,
                    "created_at": "2024-01-15T10:00:00",
                    "updated_at": "2024-01-15T10:00:00",
                }
            ],
        )

    client = make_client(handler, token="t")
    documents = client.list_documents()

    assert len(documents) == 1
    assert documents[0].id == 7
    assert documents[0].title == "Resolución 001"
    assert documents[0].issuing_body == "MAGAP"


def test_upload_file_sends_multipart_and_returns_file_metadata(tmp_path: Path):
    local = tmp_path / "norma.pdf"
    local.write_bytes(b"%PDF-1.4 fake")

    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "id": 1,
                "document_id": 3,
                "original_filename": "norma.pdf",
                "content_type": "application/pdf",
                "size_bytes": 12,
                "sha256": "abc",
                "uploaded_at": "2024-01-15T10:00:00",
            },
        )

    client = make_client(handler, token="t")
    record = client.upload_file(3, str(local))

    request = seen[0]
    assert request.method == "PUT"
    assert request.url.path == "/api/v1/documents/3/file"
    assert "multipart/form-data" in request.headers["content-type"]
    body = request.content
    assert b"norma.pdf" in body
    assert b"%PDF-1.4 fake" in body
    assert record.original_filename == "norma.pdf"
    assert record.size_bytes == 12


def test_download_file_returns_bytes():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/documents/9/file"
        return httpx.Response(
            200,
            content=b"file-bytes",
            headers={"content-type": "application/pdf"},
        )

    client = make_client(handler, token="t")
    data = client.download_file(9)

    assert data == b"file-bytes"


def test_download_file_401_raises_auth_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "No autenticado."})

    client = make_client(handler)
    with pytest.raises(AuthError):
        client.download_file(1)


def test_download_file_404_raises_not_found_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Documento no encontrado."})

    client = make_client(handler, token="t")
    with pytest.raises(NotFoundError) as exc_info:
        client.download_file(99)

    assert "Documento no encontrado." in str(exc_info.value)


def test_logout_posts_and_clears_token():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"detail": "Sesión cerrada correctamente."})

    client = make_client(handler, token="tok-xyz")
    client.logout()

    assert seen[0].method == "POST"
    assert seen[0].url.path == "/api/v1/auth/logout"
    assert authorization_header(seen[0]) == "Bearer tok-xyz"
    assert client.token is None


def test_transport_error_raises_domain_error_not_httpx():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(handler, token="t")
    with pytest.raises(ApiError) as exc_info:
        client.list_documents()

    assert not isinstance(exc_info.value, httpx.HTTPError)
    assert "No se pudo conectar con el servidor." in str(exc_info.value)


def test_auth_error_is_api_error_subclass():
    assert issubclass(AuthError, ApiError)
    assert issubclass(NotFoundError, ApiError)


# --- Admin: users ---------------------------------------------------------------


def make_user_json(
    user_id: int = 1,
    username: str = "admin",
    role: str = "admin",
    is_active: bool = True,
) -> dict:
    return {"id": user_id, "username": username, "role": role, "is_active": is_active}


def make_document_json(document_id: int = 1, title: str = "Resolución 001") -> dict:
    return {
        "id": document_id,
        "title": title,
        "issuing_body": "MAGAP",
        "description": None,
        "document_type": "Resolución",
        "country": None,
        "topic": None,
        "issued_on": None,
        "deleted_at": None,
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-01-15T10:00:00",
    }


def test_list_users_returns_user_models():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/users"
        assert request.method == "GET"
        return httpx.Response(200, json=[make_user_json(), make_user_json(2, "ana", "user", False)])

    client = make_client(handler, token="t")
    users = client.list_users()

    assert [u.username for u in users] == ["admin", "ana"]
    assert users[1].role == "user"
    assert users[1].is_active is False


def test_create_user_sends_payload_and_returns_user():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json=make_user_json(5, "nueva", "user"))

    client = make_client(handler, token="t")
    user = client.create_user(username="nueva", password="secret", role=Role.user)

    request = seen[0]
    assert request.method == "POST"
    assert request.url.path == "/api/v1/users"
    assert json.loads(request.content) == {
        "username": "nueva",
        "password": "secret",
        "role": "user",
    }
    assert user.id == 5
    assert user.role == "user"


def test_update_user_sends_only_provided_fields_including_false():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=make_user_json(3, "ana", "user", False))

    client = make_client(handler, token="t")
    user = client.update_user(3, is_active=False)

    assert seen[0].method == "PATCH"
    assert seen[0].url.path == "/api/v1/users/3"
    assert json.loads(seen[0].content) == {"is_active": False}
    assert user.is_active is False


def test_update_user_serializes_role_enum_and_username():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=make_user_json(3, "ana", "admin"))

    client = make_client(handler, token="t")
    client.update_user(3, username="ana", role=Role.admin)

    assert json.loads(seen[0].content) == {"username": "ana", "role": "admin"}


def test_update_user_omits_unset_fields():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=make_user_json())

    client = make_client(handler, token="t")
    client.update_user(1)

    assert json.loads(seen[0].content) == {}


def test_update_user_404_raises_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Usuario no encontrado."})

    client = make_client(handler, token="t")
    with pytest.raises(NotFoundError) as exc_info:
        client.update_user(99, is_active=False)

    assert "Usuario no encontrado." in str(exc_info.value)


# --- Admin: documents -----------------------------------------------------------


def test_create_document_sends_payload_and_returns_document():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json=make_document_json(10))

    client = make_client(handler, token="t")
    document = client.create_document(
        title="Resolución 001",
        issuing_body="MAGAP",
        description="Norma lactea",
        document_type="Resolución",
        country="Uruguay",
        topic="lácteos",
        issued_on="2024-01-15",
    )

    request = seen[0]
    assert request.method == "POST"
    assert request.url.path == "/api/v1/documents"
    assert json.loads(request.content) == {
        "title": "Resolución 001",
        "issuing_body": "MAGAP",
        "description": "Norma lactea",
        "document_type": "Resolución",
        "country": "Uruguay",
        "topic": "lácteos",
        "issued_on": "2024-01-15",
    }
    assert document.id == 10


def test_create_document_omits_none_optionals():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json=make_document_json(11))

    client = make_client(handler, token="t")
    client.create_document(title="Guía", issuing_body="ASEGUA")

    assert json.loads(seen[0].content) == {"title": "Guía", "issuing_body": "ASEGUA"}


def test_create_document_serializes_date_object():
    from datetime import date

    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json=make_document_json(12))

    client = make_client(handler, token="t")
    client.create_document(title="Decreto", issuing_body="MAGAP", issued_on=date(2024, 2, 1))

    assert json.loads(seen[0].content)["issued_on"] == "2024-02-01"


def test_update_document_sends_only_provided_fields():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=make_document_json(7, "Titulo nuevo"))

    client = make_client(handler, token="t")
    document = client.update_document(7, title="Titulo nuevo")

    assert seen[0].method == "PATCH"
    assert seen[0].url.path == "/api/v1/documents/7"
    assert json.loads(seen[0].content) == {"title": "Titulo nuevo"}
    assert document.title == "Titulo nuevo"


def test_update_document_with_no_fields_sends_empty_payload():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=make_document_json(7))

    client = make_client(handler, token="t")
    client.update_document(7)

    assert json.loads(seen[0].content) == {}


def test_delete_document_uses_delete_and_returns_none():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(204)

    client = make_client(handler, token="t")
    assert client.delete_document(4) is None

    assert seen[0].method == "DELETE"
    assert seen[0].url.path == "/api/v1/documents/4"


def test_restore_document_posts_and_returns_document():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=make_document_json(8))

    client = make_client(handler, token="t")
    document = client.restore_document(8)

    assert seen[0].method == "POST"
    assert seen[0].url.path == "/api/v1/documents/8/restore"
    assert document.id == 8


def test_recycle_bin_listing_passes_deleted_true():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[make_document_json(9)])

    client = make_client(handler, token="t")
    documents = client.list_documents(deleted=True)

    assert seen[0].url.params["deleted"] == "true"
    assert len(documents) == 1


def test_upload_file_bytes_sends_multipart_and_returns_file_metadata():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "id": 1,
                "document_id": 3,
                "original_filename": "norma.pdf",
                "content_type": "application/pdf",
                "size_bytes": 12,
                "sha256": "abc",
                "uploaded_at": "2024-01-15T10:00:00",
            },
        )

    client = make_client(handler, token="t")
    record = client.upload_file_bytes(3, "norma.pdf", b"%PDF-1.4 fake", "application/pdf")

    request = seen[0]
    assert request.method == "PUT"
    assert request.url.path == "/api/v1/documents/3/file"
    assert "multipart/form-data" in request.headers["content-type"]
    assert b"%PDF-1.4 fake" in request.content
    assert record.original_filename == "norma.pdf"
