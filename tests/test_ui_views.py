"""View-model and view-structure tests for shared Flet views (task 5.2)."""

from unittest.mock import MagicMock

import flet as ft
import pytest

from app.api.schemas import DocumentOut, UserOut
from app.db.models import Role
from app.ui.api_client import ApiError, AuthError, NotFoundError
from app.ui.views.catalog import FILTER_DEBOUNCE_SECONDS, CatalogView, CatalogViewModel
from app.ui.views.sign_in import SignInView, SignInViewModel

BOOTSTRAP_HINT = "python -m app.cli create-admin"


def make_user(username: str = "admin", role: Role = Role.admin) -> UserOut:
    return UserOut(id=1, username=username, role=role, is_active=True)


def make_document(
    document_id: int = 1,
    title: str = "Resolución 001",
    issuing_body: str = "MAGAP",
    document_type: str | None = "Resolución",
    country: str | None = None,
    topic: str | None = None,
) -> DocumentOut:
    return DocumentOut(
        id=document_id,
        title=title,
        issuing_body=issuing_body,
        description=None,
        document_type=document_type,
        country=country,
        topic=topic,
        issued_on=None,
        deleted_at=None,
        created_at="2024-01-15T10:00:00",
        updated_at="2024-01-15T10:00:00",
    )


def walk_controls(control, acc=None):
    acc = [] if acc is None else acc
    acc.append(control)
    for attr in ("controls", "content", "title", "actions", "appbar"):
        value = getattr(control, attr, None)
        if value is None:
            continue
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, ft.Control) or hasattr(item, "_values"):
                walk_controls(item, acc)
    return acc


def collect_text_values(control) -> list[str]:
    values = []
    for node in walk_controls(control):
        if getattr(node, "visible", True) is False:
            continue
        if isinstance(node, ft.Text) and isinstance(node.value, str):
            values.append(node.value)
        if isinstance(node, ft.TextField) and node.label:
            values.append(node.label)
        tooltip = getattr(node, "tooltip", None)
        if isinstance(tooltip, str) and tooltip:
            values.append(tooltip)
    return values


# --- SignInViewModel ---------------------------------------------------------


def test_sign_in_view_model_success():
    client = MagicMock()
    client.login.return_value = make_user()
    vm = SignInViewModel(client)

    assert vm.submit("admin", "secret") is True
    assert vm.user is not None
    assert vm.user.username == "admin"
    assert vm.error_message is None
    client.login.assert_called_once_with("admin", "secret")


def test_sign_in_view_model_auth_error_shows_spanish_and_bootstrap_hint():
    client = MagicMock()
    client.login.side_effect = AuthError("Credenciales inválidas.", status_code=401)
    vm = SignInViewModel(client)

    assert vm.submit("admin", "wrong") is False
    assert vm.error_message is not None
    assert "Credenciales inválidas." in vm.error_message
    assert vm.bootstrap_hint is not None
    assert BOOTSTRAP_HINT in vm.bootstrap_hint


def test_sign_in_view_model_generic_api_error_has_no_bootstrap_hint():
    client = MagicMock()
    client.login.side_effect = ApiError("No se pudo conectar con el servidor.")
    vm = SignInViewModel(client)

    assert vm.submit("admin", "secret") is False
    assert "No se pudo conectar con el servidor." in (vm.error_message or "")
    assert vm.bootstrap_hint is None


# --- CatalogViewModel --------------------------------------------------------


def test_catalog_refresh_passes_filters_to_client():
    client = MagicMock()
    client.list_documents.return_value = [make_document()]
    vm = CatalogViewModel(client)

    vm.query = "resolución"
    vm.document_type = "Decreto"
    vm.issuing_body = "MAGAP"
    vm.country = "Uruguay"
    vm.topic = "lácteos"
    vm.refresh()

    client.list_documents.assert_called_once_with(
        query="resolución",
        document_type="Decreto",
        issuing_body="MAGAP",
        country="Uruguay",
        topic="lácteos",
    )
    assert len(vm.documents) == 1
    assert vm.error_message is None


def test_catalog_refresh_skips_blank_filters():
    client = MagicMock()
    client.list_documents.return_value = []
    vm = CatalogViewModel(client)

    vm.query = "   "
    vm.document_type = ""
    vm.issuing_body = None  # type: ignore[assignment]
    vm.country = "  "
    vm.topic = ""
    vm.refresh()

    client.list_documents.assert_called_once_with(
        query=None,
        document_type=None,
        issuing_body=None,
        country=None,
        topic=None,
    )


def test_catalog_refresh_api_error_sets_message_and_keeps_prior_documents():
    client = MagicMock()
    client.list_documents.side_effect = [
        [make_document()],
        ApiError("No se pudo conectar con el servidor."),
    ]
    vm = CatalogViewModel(client)
    vm.refresh()
    assert len(vm.documents) == 1

    vm.refresh()
    assert len(vm.documents) == 1
    assert "No se pudo conectar con el servidor." in (vm.error_message or "")


def test_catalog_download_delegates_to_client():
    client = MagicMock()
    client.download_file.return_value = b"bytes"
    vm = CatalogViewModel(client)

    assert vm.download(9) == b"bytes"
    client.download_file.assert_called_once_with(9)


def test_catalog_download_not_found_raises_domain_error():
    client = MagicMock()
    client.download_file.side_effect = NotFoundError("Documento no encontrado.", status_code=404)
    vm = CatalogViewModel(client)

    with pytest.raises(NotFoundError):
        vm.download(99)


# --- View structure (Flet controls built offline, no Page) -------------------


def test_sign_in_view_builds_spanish_controls():
    client = MagicMock()
    view = SignInView(client, on_success=lambda: None).build()

    assert isinstance(view, ft.View)
    texts = " | ".join(collect_text_values(view))
    assert "Inicio de sesión" in texts
    assert "Usuario" in texts
    assert "Contraseña" in texts
    assert "Iniciar sesión" in texts
    assert BOOTSTRAP_HINT in texts

    fields = [n for n in walk_controls(view) if isinstance(n, ft.TextField)]
    labels = {field.label for field in fields}
    assert "Usuario" in labels
    assert "Contraseña" in labels
    password_fields = [f for f in fields if f.label == "Contraseña"]
    assert password_fields and password_fields[0].password is True


def test_catalog_view_builds_search_filters_and_rows():
    document = make_document(title="Guía Técnica", issuing_body="ASEGUA", document_type="Guía")
    client = MagicMock()
    client.list_documents.return_value = [document]

    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.vm.refresh()
    view = catalog.build()

    assert isinstance(view, ft.View)
    joined = " | ".join(collect_text_values(view))
    assert "Catálogo de documentos" in joined
    assert "Buscar" in joined
    assert "Tipo de documento" in joined
    assert "Órgano emisor" in joined
    assert "País" in joined
    assert "Tema" in joined
    assert "Guía Técnica" in joined
    assert "ASEGUA" in joined
    assert "Guía" in joined
    assert "Descargar" in joined
    assert "Cerrar sesión" in joined

    labels = {
        n.label for n in walk_controls(view) if isinstance(n, ft.TextField) and n.label
    }
    assert "Tipo de documento" in labels
    assert "Órgano emisor" in labels
    assert "País" in labels
    assert "Tema" in labels


def test_catalog_filter_fields_have_on_change_wired():
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())

    for field in (
        catalog._search_field,
        catalog._type_field,
        catalog._body_field,
        catalog._country_field,
        catalog._topic_field,
    ):
        assert field.on_change is not None


def test_catalog_filter_change_debounces_and_search_applies_immediately(monkeypatch):
    class FakeTimer:
        def __init__(self, interval, function, args=None, kwargs=None):
            self.interval = interval
            self.function = function
            self.daemon = False
            self.started = False
            self.cancelled = False

        def start(self):
            self.started = True

        def cancel(self):
            self.cancelled = True

    monkeypatch.setattr("app.ui.views.catalog.threading.Timer", FakeTimer)

    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.vm.refresh()
    catalog.build()
    client.list_documents.reset_mock()

    catalog._country_field.value = "Uruguay"
    catalog._topic_field.value = "lácteos"
    catalog._on_filter_change()
    pending = catalog._filter_timer
    assert isinstance(pending, FakeTimer)
    assert pending.interval == FILTER_DEBOUNCE_SECONDS
    assert pending.started
    client.list_documents.assert_not_called()  # debounced: not applied yet

    catalog._on_search()  # Enter/button: cancels the pending timer and applies now
    assert pending.cancelled
    assert catalog._filter_timer is None
    client.list_documents.assert_called_once_with(
        query=None,
        document_type=None,
        issuing_body=None,
        country="Uruguay",
        topic="lácteos",
    )

    pending.function()  # the debounce callback applies the same filters
    assert client.list_documents.call_count == 2


def test_catalog_view_empty_state_message():
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.vm.refresh()
    view = catalog.build()

    joined = " | ".join(collect_text_values(view))
    assert "No hay documentos." in joined


def test_catalog_view_error_state_message():
    client = MagicMock()
    client.list_documents.side_effect = ApiError("No se pudo conectar con el servidor.")
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.vm.refresh()
    view = catalog.build()

    joined = " | ".join(collect_text_values(view))
    assert "No se pudo cargar el catálogo." in joined
    assert "No se pudo conectar con el servidor." in joined
