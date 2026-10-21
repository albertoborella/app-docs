"""View-model and view-structure tests for admin Flet views (phase 6)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest

from app.api.schemas import DocumentOut, UserOut
from app.db.models import Role
from app.ui.api_client import ApiError, AuthError
from app.ui.views.document_form import (
    INVALID_DATE_MESSAGE,
    MISSING_FIELDS_MESSAGE,
    SAVED_MESSAGE,
    UPLOAD_CANCELLED_MESSAGE,
    UPLOADED_MESSAGE,
    DocumentFormView,
    DocumentFormViewModel,
)


def make_user(
    user_id: int = 1,
    username: str = "admin",
    role: Role = Role.admin,
    is_active: bool = True,
) -> UserOut:
    return UserOut(id=user_id, username=username, role=role, is_active=is_active)


def make_document(
    document_id: int = 1,
    title: str = "Resolución 001",
    issuing_body: str = "MAGAP",
    document_type: str | None = "Resolución",
    country: str | None = None,
    topic: str | None = None,
    description: str | None = None,
) -> DocumentOut:
    return DocumentOut(
        id=document_id,
        title=title,
        issuing_body=issuing_body,
        description=description,
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
    for attr in ("controls", "content", "title", "actions", "appbar", "leading"):
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


def make_file_picker(picked=None) -> MagicMock:
    picker = MagicMock()
    picker.pick_files = AsyncMock(return_value=picked or [])
    return picker


def fill_form(view: DocumentFormView, **values: str) -> None:
    view._title.value = values.get("title", "Resolución 001")
    view._issuing_body.value = values.get("issuing_body", "MAGAP")
    view._description.value = values.get("description")
    view._document_type.value = values.get("document_type")
    view._country.value = values.get("country")
    view._topic.value = values.get("topic")
    view._issued_on.value = values.get("issued_on")


# --- DocumentFormViewModel -----------------------------------------------------


def test_document_form_view_model_create_calls_create_document():
    client = MagicMock()
    client.create_document.return_value = make_document()
    vm = DocumentFormViewModel(client)

    document = vm.save(
        title="Resolución 001",
        issuing_body="MAGAP",
        description="Norma",
        document_type="Resolución",
        country="Uruguay",
        topic="lácteos",
        issued_on="2024-01-15",
    )

    client.create_document.assert_called_once_with(
        title="Resolución 001",
        issuing_body="MAGAP",
        description="Norma",
        document_type="Resolución",
        country="Uruguay",
        topic="lácteos",
        issued_on="2024-01-15",
    )
    client.update_document.assert_not_called()
    assert document.id == 1
    assert vm.document is document
    assert vm.error_message is None


def test_document_form_view_model_edit_calls_update_document_with_id():
    client = MagicMock()
    existing = make_document(document_id=7, title="Viejo")
    client.update_document.return_value = make_document(document_id=7, title="Nuevo")
    vm = DocumentFormViewModel(client, existing)

    document = vm.save(title="Nuevo", issuing_body="MAGAP")

    client.update_document.assert_called_once_with(
        7,
        title="Nuevo",
        issuing_body="MAGAP",
        description=None,
        document_type=None,
        country=None,
        topic=None,
        issued_on=None,
    )
    client.create_document.assert_not_called()
    assert document.title == "Nuevo"


def test_document_form_view_model_api_error_sets_message_and_raises():
    client = MagicMock()
    client.create_document.side_effect = ApiError("No se pudo conectar con el servidor.")
    vm = DocumentFormViewModel(client)

    with pytest.raises(ApiError):
        vm.save(title="X", issuing_body="Y")

    assert "No se pudo conectar con el servidor." in (vm.error_message or "")


def test_document_form_view_model_auth_error_marks_session_expired():
    client = MagicMock()
    client.create_document.side_effect = AuthError("No autenticado.", status_code=401)
    vm = DocumentFormViewModel(client)

    with pytest.raises(AuthError):
        vm.save(title="X", issuing_body="Y")

    assert vm.session_expired is True


def test_document_form_view_model_upload_delegates_to_client():
    client = MagicMock()
    vm = DocumentFormViewModel(client, make_document(document_id=5))

    vm.upload_from_path("/tmp/norma.pdf")
    client.upload_file.assert_called_once_with(5, "/tmp/norma.pdf")

    vm.upload_from_bytes("norma.pdf", b"data")
    client.upload_file_bytes.assert_called_once_with(5, "norma.pdf", b"data")


def test_document_form_view_model_upload_without_document_raises():
    client = MagicMock()
    vm = DocumentFormViewModel(client)

    with pytest.raises(RuntimeError):
        vm.upload_from_bytes("norma.pdf", b"data")


# --- DocumentFormView structure -------------------------------------------------


def test_document_form_create_mode_builds_spanish_controls():
    client = MagicMock()
    picker = make_file_picker()
    form = DocumentFormView(
        client,
        file_picker=picker,
        on_back=lambda: None,
        on_saved=lambda: None,
    )
    view = form.build()

    assert isinstance(view, ft.View)
    joined = " | ".join(collect_text_values(view))
    assert "Nuevo documento" in joined
    assert "Guardar" in joined
    assert "Adjuntar archivo" in joined
    assert "Volver al catálogo" in joined

    labels = {
        n.label for n in walk_controls(view) if isinstance(n, ft.TextField) and n.label
    }
    assert labels == {
        "Título",
        "Órgano emisor",
        "Descripción",
        "Tipo de documento",
        "País",
        "Tema",
        "Fecha de emisión",
    }


def test_document_form_edit_mode_prefills_and_titles():
    client = MagicMock()
    existing = make_document(
        document_id=9,
        title="Guía Técnica",
        issuing_body="ASEGUA",
        description="Detalle",
        country="Uruguay",
        topic="lácteos",
    )
    form = DocumentFormView(
        client,
        document=existing,
        file_picker=make_file_picker(),
        on_back=lambda: None,
        on_saved=lambda: None,
    )
    view = form.build()

    joined = " | ".join(collect_text_values(view))
    assert "Editar documento" in joined
    assert form._title.value == "Guía Técnica"
    assert form._issuing_body.value == "ASEGUA"
    assert form._country.value == "Uruguay"


def test_document_form_back_button_calls_on_back():
    calls: list[str] = []
    client = MagicMock()
    form = DocumentFormView(
        client,
        file_picker=make_file_picker(),
        on_back=lambda: calls.append("back"),
        on_saved=lambda: None,
    )
    view = form.build()

    back_buttons = [
        n
        for n in walk_controls(view)
        if isinstance(n, ft.IconButton) and n.tooltip == "Volver al catálogo"
    ]
    assert len(back_buttons) == 1
    back_buttons[0].on_click()
    assert calls == ["back"]


# --- DocumentFormView flows -------------------------------------------------------


def test_document_form_save_create_validates_required_fields():
    client = MagicMock()
    notices: list[str] = []
    form = DocumentFormView(
        client,
        file_picker=make_file_picker(),
        on_back=lambda: None,
        on_saved=lambda: None,
        on_notice=notices.append,
    )
    form._title.value = "   "
    form._issuing_body.value = "MAGAP"

    asyncio.run(form._on_save())

    client.create_document.assert_not_called()
    assert form._error_text.visible is True
    assert MISSING_FIELDS_MESSAGE in (form._error_text.value or "")


def test_document_form_save_rejects_invalid_date():
    client = MagicMock()
    form = DocumentFormView(
        client,
        file_picker=make_file_picker(),
        on_back=lambda: None,
        on_saved=lambda: None,
    )
    fill_form(form, issued_on="15/01/2024")

    asyncio.run(form._on_save())

    client.create_document.assert_not_called()
    assert INVALID_DATE_MESSAGE in (form._error_text.value or "")


def test_document_form_save_create_notices_and_prompts_upload():
    client = MagicMock()
    client.create_document.return_value = make_document(document_id=4)
    notices: list[str] = []
    picker = make_file_picker(picked=[])
    form = DocumentFormView(
        client,
        file_picker=picker,
        on_back=lambda: None,
        on_saved=lambda: None,
        on_notice=notices.append,
    )
    fill_form(form, issued_on="2024-01-15")

    asyncio.run(form._on_save())

    assert client.create_document.called
    assert picker.pick_files.called
    assert SAVED_MESSAGE in notices
    assert UPLOAD_CANCELLED_MESSAGE in notices


def test_document_form_upload_uses_path_when_available():
    client = MagicMock()
    picked = MagicMock()
    picked.path = "/tmp/norma.pdf"
    picked.name = "norma.pdf"
    picked.bytes = None
    notices: list[str] = []
    form = DocumentFormView(
        client,
        document=make_document(document_id=6),
        file_picker=make_file_picker(picked=[picked]),
        on_back=lambda: None,
        on_saved=lambda: None,
        on_notice=notices.append,
    )

    asyncio.run(form._on_upload())

    client.upload_file.assert_called_once_with(6, "/tmp/norma.pdf")
    assert UPLOADED_MESSAGE in notices


def test_document_form_upload_uses_bytes_when_no_path():
    client = MagicMock()
    picked = MagicMock()
    picked.path = None
    picked.name = "norma.pdf"
    picked.bytes = b"%PDF"
    notices: list[str] = []
    form = DocumentFormView(
        client,
        document=make_document(document_id=6),
        file_picker=make_file_picker(picked=[picked]),
        on_back=lambda: None,
        on_saved=lambda: None,
        on_notice=notices.append,
    )

    asyncio.run(form._on_upload())

    client.upload_file_bytes.assert_called_once_with(6, "norma.pdf", b"%PDF")
    assert UPLOADED_MESSAGE in notices


def test_document_form_upload_api_error_notices_spanish_message():
    client = MagicMock()
    client.upload_file_bytes.side_effect = ApiError("Tipo de archivo no permitido.")
    picked = MagicMock()
    picked.path = None
    picked.name = "malware.exe"
    picked.bytes = b"zz"
    notices: list[str] = []
    form = DocumentFormView(
        client,
        document=make_document(),
        file_picker=make_file_picker(picked=[picked]),
        on_back=lambda: None,
        on_saved=lambda: None,
        on_notice=notices.append,
    )

    asyncio.run(form._on_upload())

    assert any("Tipo de archivo no permitido." in n for n in notices)


def test_document_form_save_edit_does_not_prompt_upload():
    client = MagicMock()
    client.update_document.return_value = make_document(title="Nuevo")
    picker = make_file_picker()
    notices: list[str] = []
    form = DocumentFormView(
        client,
        document=make_document(),
        file_picker=picker,
        on_back=lambda: None,
        on_saved=lambda: None,
        on_notice=notices.append,
    )
    fill_form(form, title="Nuevo")

    asyncio.run(form._on_save())

    assert client.update_document.called
    assert not picker.pick_files.called
    assert SAVED_MESSAGE in notices


def test_document_form_session_expired_invokes_callback():
    client = MagicMock()
    client.create_document.side_effect = AuthError("No autenticado.", status_code=401)
    expired: list[str] = []
    form = DocumentFormView(
        client,
        file_picker=make_file_picker(),
        on_back=lambda: None,
        on_saved=lambda: None,
        on_session_expired=lambda: expired.append("sign-in"),
    )
    fill_form(form)

    asyncio.run(form._on_save())

    assert expired == ["sign-in"]
