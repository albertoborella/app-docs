"""Contract tests for the UI API client (task 5.1) — mocked httpx, no network."""

from pathlib import Path

import httpx
import pytest

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
        deleted=True,
    )

    url = seen[0].url
    assert url.path == "/api/v1/documents"
    assert url.params["query"] == "resolución"
    assert url.params["document_type"] == "Decreto"
    assert url.params["issuing_body"] == "MAGAP"
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
