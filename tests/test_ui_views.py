"""View-model and view-structure tests for shared Flet views (task 5.2)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest

from app.api.schemas import DocumentOut, UserOut
from app.db.models import Role
from app.ui.api_client import ApiError, AuthError, NotFoundError
from app.ui.theme import (
    THEME_TOGGLE_TOOLTIP,
    next_theme_mode,
    restore_theme_mode,
    theme_toggle_button,
)
from app.ui.views.catalog import (
    FILTER_DEBOUNCE_SECONDS,
    MOBILE_BREAKPOINT_PX,
    OPEN_NOTICE_MESSAGE,
    CatalogView,
    CatalogViewModel,
)
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


def test_catalog_refresh_passes_query_to_client():
    client = MagicMock()
    client.list_documents.return_value = [make_document()]
    vm = CatalogViewModel(client)

    vm.query = "resolución"
    vm.refresh()

    client.list_documents.assert_called_once_with(query="resolución")
    assert len(vm.documents) == 1
    assert vm.error_message is None


def test_catalog_refresh_skips_blank_filters():
    client = MagicMock()
    client.list_documents.return_value = []
    vm = CatalogViewModel(client)

    vm.query = "   "
    vm.refresh()

    client.list_documents.assert_called_once_with(query=None)


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


def test_catalog_view_builds_search_field_and_rows():
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
    assert "Guía Técnica" in joined
    assert "ASEGUA" in joined
    assert "Guía" in joined
    assert "Descargar" in joined
    assert "Cerrar sesión" in joined

    labels = {
        n.label for n in walk_controls(view) if isinstance(n, ft.TextField) and n.label
    }
    assert "Buscar" in labels
    removed_labels = {"Tipo de documento", "Órgano emisor", "País", "Tema"}
    assert labels.isdisjoint(removed_labels)
    assert not removed_labels & set(collect_text_values(view))


def test_catalog_filter_fields_have_on_change_wired():
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())

    assert catalog._search_field.on_change is not None


def test_catalog_filter_change_debounces_and_search_applies_immediately(monkeypatch):
    assert FILTER_DEBOUNCE_SECONDS == 0.3  # exported debounce contract
    monkeypatch.setattr("app.ui.views.catalog.FILTER_DEBOUNCE_SECONDS", 0)
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.vm.refresh()
    catalog.build()
    client.list_documents.reset_mock()

    async def scenario():
        catalog._search_field.value = "resolución"
        await catalog._on_filter_change()
        pending = catalog._filter_task
        assert pending is not None
        client.list_documents.assert_not_called()  # debounced: not applied yet

        await catalog._on_search()  # Enter/button: cancels pending, applies now
        assert catalog._filter_task is None
        client.list_documents.assert_called_once_with(query="resolución")

        catalog._filter_task = None
        await catalog._on_filter_change()  # debounce path applies the same query
        await catalog._filter_task
        assert client.list_documents.call_count == 2
        client.list_documents.assert_called_with(query="resolución")

    asyncio.run(scenario())


def test_catalog_download_click_handler_is_async():
    import inspect
    from functools import partial

    client = MagicMock()
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    row = catalog._document_row(make_document())
    # find the FilledButton whose content text is "Descargar" by walking controls
    buttons = [n for n in walk_controls(row) if isinstance(n, ft.FilledButton)]
    assert len(buttons) == 1
    handler = buttons[0].on_click
    assert isinstance(handler, partial)
    assert inspect.iscoroutinefunction(handler)


def test_apply_filters_pushes_update_or_noops_offline():
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.build()
    asyncio.run(catalog._apply_filters())  # offline: _push_update must not raise
    assert client.list_documents.called


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


# --- Catalog web mode: direct open (Option B) ---------------------------------


def test_file_url_builds_api_url_with_quoted_token_and_inline():
    client = MagicMock()
    client.base_url = "http://192.168.0.83:8550"
    client.public_base_url = "http://192.168.0.83:8550"
    client.token = "abc+/=def"  # characters that must be percent-encoded
    catalog = CatalogView(
        client, on_sign_out=lambda: None, file_picker=ft.FilePicker(), web=True
    )

    url = catalog._file_url(make_document(document_id=7))

    assert url == (
        "http://192.168.0.83:8550/api/v1/documents/7/file"
        "?token=abc%2B%2F%3Ddef&inline=true"
    )


def test_file_url_with_missing_token_yields_empty_token_param():
    client = MagicMock()
    client.base_url = "http://127.0.0.1:8000"
    client.public_base_url = "http://127.0.0.1:8000"
    client.token = None
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())

    url = catalog._file_url(make_document(document_id=3))

    assert url == "http://127.0.0.1:8000/api/v1/documents/3/file?token=&inline=true"


def test_web_mode_row_button_opens_url_in_new_tab(monkeypatch):
    # ft.OpenUrl requires an active page context; stub it to capture url/target offline.
    captured: dict = {}

    class _StubOpenUrl:
        def __init__(self, url, target=None):
            captured["url"] = url
            captured["target"] = target

    monkeypatch.setattr("app.ui.views.catalog.ft.OpenUrl", _StubOpenUrl)
    client = MagicMock()
    client.base_url = "http://192.168.0.83:8550"
    client.public_base_url = "http://192.168.0.83:8550"
    client.token = "tok"
    catalog = CatalogView(
        client, on_sign_out=lambda: None, file_picker=ft.FilePicker(), web=True
    )
    row = catalog._document_row(make_document(document_id=9))

    buttons = [n for n in walk_controls(row) if isinstance(n, ft.FilledButton)]
    assert len(buttons) == 1
    button = buttons[0]
    assert button.on_click == catalog._on_open_click  # notice only, no byte fetch
    assert isinstance(button.action, _StubOpenUrl)
    assert captured["url"] == (
        "http://192.168.0.83:8550/api/v1/documents/9/file?token=tok&inline=true"
    )
    assert captured["target"] == ft.UrlTarget.BLANK
    assert "Abrir" in collect_text_values(row)
    assert button.icon == ft.Icons.OPEN_IN_NEW


def test_web_mode_open_button_notices_how_to_come_back():
    client = MagicMock()
    notices: list[str] = []
    catalog = CatalogView(
        client,
        on_sign_out=lambda: None,
        file_picker=ft.FilePicker(),
        on_notice=notices.append,
        web=True,
    )

    catalog._on_open_click()

    assert notices == [OPEN_NOTICE_MESSAGE]


def test_default_mode_is_desktop_download_button():
    client = MagicMock()
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())

    assert catalog.web is False
    row = catalog._document_row(make_document())
    buttons = [n for n in walk_controls(row) if isinstance(n, ft.FilledButton)]
    assert len(buttons) == 1
    assert buttons[0].on_click is not None
    assert buttons[0].action is None
    assert "Descargar" in collect_text_values(row)


# --- Theme toggle -----------------------------------------------------------


def test_next_theme_mode_flips_light_dark_and_system():
    assert next_theme_mode(ft.ThemeMode.LIGHT) == ft.ThemeMode.DARK
    assert next_theme_mode(ft.ThemeMode.DARK) == ft.ThemeMode.LIGHT
    assert next_theme_mode(ft.ThemeMode.SYSTEM) == ft.ThemeMode.DARK
    assert next_theme_mode(None) == ft.ThemeMode.DARK


def test_theme_toggle_click_is_noop_when_unmounted():
    button = theme_toggle_button()

    asyncio.run(button.on_click(None))

    assert button.tooltip == THEME_TOGGLE_TOOLTIP


def test_catalog_appbar_has_theme_toggle_before_logout():
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.vm.refresh()
    view = catalog.build()

    tooltips = [
        n.tooltip for n in walk_controls(view) if isinstance(n, ft.IconButton)
    ]
    assert THEME_TOGGLE_TOOLTIP in tooltips
    assert tooltips.index(THEME_TOGGLE_TOOLTIP) < tooltips.index("Cerrar sesión")


def test_catalog_loading_ring_present_and_hidden_by_default():
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.vm.refresh()
    view = catalog.build()

    rings = [n for n in walk_controls(view) if isinstance(n, ft.ProgressRing)]
    assert len(rings) == 1
    assert rings[0].visible is False


def test_catalog_loading_ring_toggles_and_filters_leave_it_hidden():
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(client, on_sign_out=lambda: None, file_picker=ft.FilePicker())
    catalog.build()

    catalog._set_loading(True)
    assert catalog._loading_ring.visible is True
    catalog._set_loading(False)
    assert catalog._loading_ring.visible is False

    asyncio.run(catalog._apply_filters())
    assert catalog._loading_ring.visible is False
    assert client.list_documents.called


# --- Theme persistence -------------------------------------------------------


def test_restore_theme_mode_applies_stored_preference():
    prefs = MagicMock()
    prefs.get = AsyncMock(return_value="dark")
    page = MagicMock()

    asyncio.run(restore_theme_mode(page, prefs))

    assert page.theme_mode == ft.ThemeMode.DARK
    page.update.assert_called_once()


def test_restore_theme_mode_keeps_system_when_nothing_stored():
    prefs = MagicMock()
    prefs.get = AsyncMock(return_value=None)
    page = MagicMock()

    asyncio.run(restore_theme_mode(page, prefs))

    page.update.assert_not_called()


def test_restore_theme_mode_swallows_storage_errors():
    prefs = MagicMock()
    prefs.get = AsyncMock(side_effect=RuntimeError("client gone"))
    page = MagicMock()

    asyncio.run(restore_theme_mode(page, prefs))

    page.update.assert_not_called()


# --- Responsive document rows ------------------------------------------------


def test_narrow_viewport_puts_buttons_below_stacked_full_width():
    client = MagicMock()
    client.list_documents.return_value = []
    catalog = CatalogView(
        client,
        on_sign_out=lambda: None,
        file_picker=ft.FilePicker(),
        is_admin=True,
        viewport_width=375,
    )

    card = catalog._document_row(make_document(title="Resolución 001"))
    top = card.content.content

    assert isinstance(top, ft.Column)
    assert len(top.controls) == 2
    info, buttons = top.controls
    assert isinstance(info, ft.Column)
    assert isinstance(buttons, ft.Column)
    assert buttons.horizontal_alignment == ft.CrossAxisAlignment.STRETCH
    labels = collect_text_values(buttons)
    assert "Descargar" in labels
    assert "Editar" in labels
    assert "Quitar" in labels


def test_wide_viewport_keeps_side_by_side_layout():
    client = MagicMock()
    catalog = CatalogView(
        client,
        on_sign_out=lambda: None,
        file_picker=ft.FilePicker(),
        is_admin=True,
        viewport_width=1024,
    )

    card = catalog._document_row(make_document())
    top = card.content.content

    assert isinstance(top, ft.Row)
    assert top.alignment == ft.MainAxisAlignment.SPACE_BETWEEN


def test_breakpoint_boundary_and_unknown_width():
    client = MagicMock()
    wide = CatalogView(
        client, on_sign_out=lambda: None, file_picker=ft.FilePicker(),
        viewport_width=MOBILE_BREAKPOINT_PX,
    )
    narrow = CatalogView(
        client, on_sign_out=lambda: None, file_picker=ft.FilePicker(),
        viewport_width=MOBILE_BREAKPOINT_PX - 1,
    )
    unknown = CatalogView(
        client, on_sign_out=lambda: None, file_picker=ft.FilePicker(),
    )

    assert wide._is_narrow() is False
    assert narrow._is_narrow() is True
    assert unknown._is_narrow() is False


def test_set_viewport_width_rebuilds_rows_in_place():
    client = MagicMock()
    client.list_documents.return_value = [make_document()]
    catalog = CatalogView(
        client,
        on_sign_out=lambda: None,
        file_picker=ft.FilePicker(),
        viewport_width=1024,
    )
    catalog.vm.refresh()
    catalog.build()
    assert isinstance(catalog._rows.controls[0].content.content, ft.Row)

    catalog.set_viewport_width(400)

    assert isinstance(catalog._rows.controls[0].content.content, ft.Column)
