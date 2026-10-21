"""HTTP API client for the dairy document manager UI (httpx + bearer token).

One client path for every deployment target (web, desktop, mobile) per design.md.
"""

from __future__ import annotations

import mimetypes
import os
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from app.api.schemas import DocumentOut, FileOut, UserOut
from app.db.models import Role

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
_API_PREFIX = "/api/v1"
_TIMEOUT_SECONDS = 30.0

_FALLBACK_AUTH_MESSAGE = "No autenticado."
_FALLBACK_DETAIL_MESSAGE = "No se pudo completar la operación."
_TRANSPORT_MESSAGE = "No se pudo conectar con el servidor."


class ApiError(Exception):
    """Domain error for API client failures (never leaks raw httpx errors)."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthError(ApiError):
    """401 — missing, invalid, or expired credentials."""


class NotFoundError(ApiError):
    """404 — resource hidden or absent."""


class ApiClient:
    """Synchronous httpx client with bearer-token auth."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = _TIMEOUT_SECONDS,
    ) -> None:
        resolved = base_url or os.environ.get("DOCMANAGER_API_URL") or DEFAULT_BASE_URL
        self.base_url = resolved.rstrip("/")
        self.token = token
        self._client = httpx.Client(
            base_url=self.base_url,
            transport=transport,
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def login(self, username: str, password: str) -> UserOut:
        """POST /auth/login — stores the bearer token and returns the user."""
        data = self._request(
            "POST",
            f"{_API_PREFIX}/auth/login",
            json={"username": username, "password": password},
            authenticated=False,
        )
        self.token = data["token"]
        return UserOut.model_validate(data["user"])

    def logout(self) -> None:
        """POST /auth/logout — ends the server-side session and clears the token."""
        self._request("POST", f"{_API_PREFIX}/auth/logout")
        self.token = None

    def list_users(self) -> list[UserOut]:
        """GET /users — admin-only account listing."""
        data = self._request("GET", f"{_API_PREFIX}/users")
        return [UserOut.model_validate(item) for item in data]

    def create_user(self, *, username: str, password: str, role: Role) -> UserOut:
        """POST /users — admin-only account provisioning."""
        data = self._request(
            "POST",
            f"{_API_PREFIX}/users",
            json={"username": username, "password": password, "role": role.value},
        )
        return UserOut.model_validate(data)

    def update_user(
        self,
        user_id: int,
        *,
        username: str | None = None,
        password: str | None = None,
        role: Role | None = None,
        is_active: bool | None = None,
    ) -> UserOut:
        """PATCH /users/{id} — admin-only edit; omits unset fields (server PATCH)."""
        payload: dict[str, Any] = {}
        if username is not None:
            payload["username"] = username
        if password is not None:
            payload["password"] = password
        if role is not None:
            payload["role"] = role.value
        if is_active is not None:
            payload["is_active"] = is_active
        data = self._request("PATCH", f"{_API_PREFIX}/users/{user_id}", json=payload)
        return UserOut.model_validate(data)

    def list_documents(
        self,
        *,
        query: str | None = None,
        document_type: str | None = None,
        issuing_body: str | None = None,
        country: str | None = None,
        topic: str | None = None,
        deleted: bool | None = None,
    ) -> list[DocumentOut]:
        """GET /documents with optional free-text search and filters."""
        params: dict[str, str] = {}
        if query is not None:
            params["query"] = query
        if document_type is not None:
            params["document_type"] = document_type
        if issuing_body is not None:
            params["issuing_body"] = issuing_body
        if country is not None:
            params["country"] = country
        if topic is not None:
            params["topic"] = topic
        if deleted is not None:
            params["deleted"] = "true" if deleted else "false"
        data = self._request("GET", f"{_API_PREFIX}/documents", params=params)
        return [DocumentOut.model_validate(item) for item in data]

    def create_document(
        self,
        *,
        title: str,
        issuing_body: str,
        description: str | None = None,
        document_type: str | None = None,
        country: str | None = None,
        topic: str | None = None,
        issued_on: date | str | None = None,
    ) -> DocumentOut:
        """POST /documents — admin-only metadata creation."""
        payload: dict[str, Any] = {"title": title, "issuing_body": issuing_body}
        if description is not None:
            payload["description"] = description
        if document_type is not None:
            payload["document_type"] = document_type
        if country is not None:
            payload["country"] = country
        if topic is not None:
            payload["topic"] = topic
        if issued_on is not None:
            payload["issued_on"] = (
                issued_on.isoformat() if isinstance(issued_on, date) else issued_on
            )
        data = self._request("POST", f"{_API_PREFIX}/documents", json=payload)
        return DocumentOut.model_validate(data)

    def update_document(
        self,
        document_id: int,
        *,
        title: str | None = None,
        issuing_body: str | None = None,
        description: str | None = None,
        document_type: str | None = None,
        country: str | None = None,
        topic: str | None = None,
        issued_on: date | str | None = None,
    ) -> DocumentOut:
        """PATCH /documents/{id} — admin-only edit; omits unset fields (server PATCH)."""
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if issuing_body is not None:
            payload["issuing_body"] = issuing_body
        if description is not None:
            payload["description"] = description
        if document_type is not None:
            payload["document_type"] = document_type
        if country is not None:
            payload["country"] = country
        if topic is not None:
            payload["topic"] = topic
        if issued_on is not None:
            payload["issued_on"] = (
                issued_on.isoformat() if isinstance(issued_on, date) else issued_on
            )
        data = self._request("PATCH", f"{_API_PREFIX}/documents/{document_id}", json=payload)
        return DocumentOut.model_validate(data)

    def delete_document(self, document_id: int) -> None:
        """DELETE /documents/{id} — admin-only soft delete (204)."""
        self._request("DELETE", f"{_API_PREFIX}/documents/{document_id}")

    def restore_document(self, document_id: int) -> DocumentOut:
        """POST /documents/{id}/restore — admin-only soft-delete undo."""
        data = self._request("POST", f"{_API_PREFIX}/documents/{document_id}/restore")
        return DocumentOut.model_validate(data)

    def upload_file(self, document_id: int, local_path: str) -> FileOut:
        """PUT /documents/{id}/file — multipart upload/replace (admin)."""
        path = Path(local_path)
        content_type, _mimetype = mimetypes.guess_type(path.name)
        with path.open("rb") as handle:
            return self._upload_multipart(document_id, path.name, handle, content_type)

    def upload_file_bytes(
        self,
        document_id: int,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> FileOut:
        """PUT /documents/{id}/file — in-memory upload/replace (admin, web picker path)."""
        return self._upload_multipart(document_id, filename, content, content_type)

    def _upload_multipart(
        self,
        document_id: int,
        filename: str,
        file_part: Any,
        content_type: str | None,
    ) -> FileOut:
        data = self._request(
            "PUT",
            f"{_API_PREFIX}/documents/{document_id}/file",
            files={"file": (filename, file_part, content_type or "application/octet-stream")},
        )
        return FileOut.model_validate(data)

    def download_file(self, document_id: int) -> bytes:
        """GET /documents/{id}/file — returns raw file bytes."""
        response = self._send(
            "GET",
            f"{_API_PREFIX}/documents/{document_id}/file",
            params=None,
            json=None,
            files=None,
            authenticated=True,
        )
        self._raise_for_status(response)
        return response.content

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> Any:
        response = self._send(
            method,
            path,
            params=params,
            json=json,
            files=files,
            authenticated=authenticated,
        )
        self._raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def _send(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None,
        json: dict[str, Any] | None,
        files: dict[str, Any] | None,
        authenticated: bool,
    ) -> httpx.Response:
        headers: dict[str, str] = {}
        if authenticated:
            if not self.token:
                raise AuthError(_FALLBACK_AUTH_MESSAGE, status_code=401)
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            return self._client.request(
                method,
                path,
                params=params,
                json=json,
                files=files,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            raise ApiError(_TRANSPORT_MESSAGE) from exc

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        detail = _error_detail(response)
        if response.status_code == 401:
            raise AuthError(detail, status_code=401)
        if response.status_code == 404:
            raise NotFoundError(detail, status_code=404)
        raise ApiError(detail, status_code=response.status_code)


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return _FALLBACK_DETAIL_MESSAGE
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str) and detail:
            return detail
    return _FALLBACK_DETAIL_MESSAGE
