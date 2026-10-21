"""View-model and view-structure tests for admin Flet views (phase 6)."""

import asyncio
from datetime import datetime
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
from app.ui.views.recycle_bin import (
    EMPTY_MESSAGE,
    LOAD_ERROR_MESSAGE,
    RESTORE_ERROR_MESSAGE,
    RESTORED_MESSAGE,
    RecycleBinView,
    RecycleBinViewModel,
)
from app.ui.views.users import (
    CREATED_MESSAGE,
    MISSING_CREDENTIALS_MESSAGE,
    MISSING_USERNAME_MESSAGE,
    SAVE_ERROR_MESSAGE,
    UserFormView,
    UserFormViewModel,
    UsersView,
    UsersViewModel,
)
from app.ui.views.users import SAVED_MESSAGE as USER_SAVED_MESSAGE


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
        if isinstance(node, (ft.TextField, ft.Dropdown, ft.Switch)) and node.label:
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


# --- RecycleBinViewModel --------------------------------------------------------


def test_recycle_bin_refresh_lists_deleted_documents_only():
    client = MagicMock()
    deleted = make_document(document_id=3, title="Retirada")
    deleted.deleted_at = None  # VM does not inspect the flag; the query does
    client.list_documents.return_value = [deleted]
    vm = RecycleBinViewModel(client)

    vm.refresh()

    client.list_documents.assert_called_once_with(deleted=True)
    assert len(vm.documents) == 1
    assert vm.error_message is None


def test_recycle_bin_refresh_api_error_sets_spanish_message():
    client = MagicMock()
    client.list_documents.side_effect = ApiError("No se pudo conectar con el servidor.")
    vm = RecycleBinViewModel(client)

    vm.refresh()

    assert vm.documents == []
    assert LOAD_ERROR_MESSAGE not in (vm.error_message or "")
    assert "No se pudo conectar con el servidor." in (vm.error_message or "")


def test_recycle_bin_refresh_auth_error_marks_session_expired():
    client = MagicMock()
    client.list_documents.side_effect = AuthError("No autenticado.", status_code=401)
    vm = RecycleBinViewModel(client)

    vm.refresh()

    assert vm.session_expired is True


def test_recycle_bin_restore_delegates_to_client():
    client = MagicMock()
    client.restore_document.return_value = make_document(document_id=3)
    vm = RecycleBinViewModel(client)

    document = vm.restore(3)

    client.restore_document.assert_called_once_with(3)
    assert document.id == 3


def test_recycle_bin_restore_auth_error_marks_session_expired():
    client = MagicMock()
    client.restore_document.side_effect = AuthError("No autenticado.", status_code=401)
    vm = RecycleBinViewModel(client)

    with pytest.raises(AuthError):
        vm.restore(3)

    assert vm.session_expired is True


# --- RecycleBinView structure and flows -------------------------------------------


def make_deleted_document() -> DocumentOut:
    document = make_document(document_id=4, title="Obsoleta")
    document.deleted_at = datetime(2024, 2, 1, 9, 30)
    return document


def test_recycle_bin_view_builds_spanish_controls_and_restore_buttons():
    client = MagicMock()
    client.list_documents.return_value = [make_deleted_document()]
    bin_view = RecycleBinView(client, on_back=lambda: None)
    bin_view.vm.refresh()
    view = bin_view.build()

    joined = " | ".join(collect_text_values(view))
    assert "Papelera de reciclaje" in joined
    assert "Obsoleta" in joined
    assert "Restaurar" in joined
    assert "Volver al catálogo" in joined

    buttons = [n for n in walk_controls(view) if isinstance(n, ft.FilledButton)]
    assert len(buttons) == 1


def test_recycle_bin_view_empty_state_message():
    client = MagicMock()
    client.list_documents.return_value = []
    bin_view = RecycleBinView(client, on_back=lambda: None)
    bin_view.vm.refresh()
    view = bin_view.build()

    joined = " | ".join(collect_text_values(view))
    assert EMPTY_MESSAGE in joined


def test_recycle_bin_view_error_state_message():
    client = MagicMock()
    client.list_documents.side_effect = ApiError("No se pudo conectar con el servidor.")
    bin_view = RecycleBinView(client, on_back=lambda: None)
    bin_view.vm.refresh()
    view = bin_view.build()

    joined = " | ".join(collect_text_values(view))
    assert "No se pudo cargar la papelera." in joined
    assert "No se pudo conectar con el servidor." in joined


def test_recycle_bin_back_button_calls_on_back():
    calls: list[str] = []
    client = MagicMock()
    client.list_documents.return_value = []
    bin_view = RecycleBinView(client, on_back=lambda: calls.append("back"))
    view = bin_view.build()

    back_buttons = [
        n
        for n in walk_controls(view)
        if isinstance(n, ft.IconButton) and n.tooltip == "Volver al catálogo"
    ]
    assert len(back_buttons) == 1
    back_buttons[0].on_click()
    assert calls == ["back"]


def test_recycle_bin_restore_click_restores_notices_and_reloads():
    client = MagicMock()
    client.list_documents.side_effect = [[make_deleted_document()], []]
    client.restore_document.return_value = make_document(document_id=4)
    notices: list[str] = []
    bin_view = RecycleBinView(client, on_back=lambda: None, on_notice=notices.append)
    bin_view.vm.refresh()
    bin_view.build()

    asyncio.run(bin_view._on_restore(make_deleted_document()))

    client.restore_document.assert_called_once_with(4)
    assert client.list_documents.call_count == 2  # initial + reload
    assert RESTORED_MESSAGE in notices
    assert bin_view._rows.controls == []


def test_recycle_bin_restore_api_error_notices_spanish_message():
    client = MagicMock()
    client.restore_document.side_effect = ApiError("Documento no encontrado.")
    notices: list[str] = []
    bin_view = RecycleBinView(client, on_back=lambda: None, on_notice=notices.append)

    asyncio.run(bin_view._on_restore(make_deleted_document()))

    assert any(RESTORE_ERROR_MESSAGE in n and "Documento no encontrado." in n for n in notices)


def test_recycle_bin_restore_auth_error_invokes_session_expired():
    client = MagicMock()
    client.restore_document.side_effect = AuthError("No autenticado.", status_code=401)
    expired: list[str] = []
    bin_view = RecycleBinView(
        client, on_back=lambda: None, on_session_expired=lambda: expired.append("sign-in")
    )

    asyncio.run(bin_view._on_restore(make_deleted_document()))

    assert expired == ["sign-in"]


# --- UsersViewModel --------------------------------------------------------------


def test_users_refresh_delegates_to_client():
    client = MagicMock()
    client.list_users.return_value = [make_user(), make_user(2, "ana", Role.user, False)]
    vm = UsersViewModel(client)

    vm.refresh()

    client.list_users.assert_called_once_with()
    assert [u.username for u in vm.users] == ["admin", "ana"]
    assert vm.error_message is None


def test_users_refresh_api_error_sets_spanish_message():
    client = MagicMock()
    client.list_users.side_effect = ApiError("No se pudo conectar con el servidor.")
    vm = UsersViewModel(client)

    vm.refresh()

    assert vm.users == []
    assert "No se pudo conectar con el servidor." in (vm.error_message or "")


def test_users_refresh_auth_error_marks_session_expired():
    client = MagicMock()
    client.list_users.side_effect = AuthError("No autenticado.", status_code=401)
    vm = UsersViewModel(client)

    vm.refresh()

    assert vm.session_expired is True


# --- UserFormViewModel ------------------------------------------------------------


def test_user_form_view_model_create_calls_create_user():
    client = MagicMock()
    client.create_user.return_value = make_user(5, "nueva", Role.user)
    vm = UserFormViewModel(client)

    user = vm.save(username="nueva", password="secret", role=Role.user, is_active=True)

    client.create_user.assert_called_once_with(username="nueva", password="secret", role=Role.user)
    client.update_user.assert_not_called()
    assert user.id == 5
    assert vm.user is user


def test_user_form_view_model_edit_calls_update_user_with_fields():
    client = MagicMock()
    existing = make_user(3, "ana", Role.user, is_active=False)
    client.update_user.return_value = make_user(3, "ana", Role.admin, is_active=True)
    vm = UserFormViewModel(client, existing)

    vm.save(username="ana", password="newpass", role=Role.admin, is_active=True)

    client.update_user.assert_called_once_with(
        3, username="ana", password="newpass", role=Role.admin, is_active=True
    )
    client.create_user.assert_not_called()


def test_user_form_view_model_edit_omits_blank_password():
    client = MagicMock()
    client.update_user.return_value = make_user(3)
    vm = UserFormViewModel(client, make_user(3))

    vm.save(username="ana", password=None, role=Role.user, is_active=False)

    assert client.update_user.call_args.kwargs["password"] is None
    assert client.update_user.call_args.kwargs["is_active"] is False


def test_user_form_view_model_auth_error_marks_session_expired():
    client = MagicMock()
    client.create_user.side_effect = AuthError("No autenticado.", status_code=401)
    vm = UserFormViewModel(client)

    with pytest.raises(AuthError):
        vm.save(username="x", password="y", role=Role.user, is_active=True)

    assert vm.session_expired is True


def test_user_form_view_model_api_error_sets_message():
    client = MagicMock()
    client.create_user.side_effect = ApiError("El nombre de usuario ya existe.")
    vm = UserFormViewModel(client)

    with pytest.raises(ApiError):
        vm.save(username="x", password="y", role=Role.user, is_active=True)

    assert "El nombre de usuario ya existe." in (vm.error_message or "")


# --- UsersView structure -----------------------------------------------------------


def test_users_view_builds_spanish_controls_and_rows():
    client = MagicMock()
    client.list_users.return_value = [
        make_user(1, "admin", Role.admin, True),
        make_user(2, "ana", Role.user, False),
    ]
    users_view = UsersView(
        client, on_back=lambda: None, on_create=lambda: None, on_edit=lambda u: None
    )
    users_view.vm.refresh()
    view = users_view.build()

    joined = " | ".join(collect_text_values(view))
    assert "Gestión de cuentas" in joined
    assert "admin" in joined
    assert "ana" in joined
    assert "Administrador" in joined
    assert "Usuario normal" in joined
    assert "Inactivo" in joined
    assert "Editar" in joined
    assert "Nuevo usuario" in joined
    assert "Volver al catálogo" in joined


def test_users_view_empty_state_message():
    client = MagicMock()
    client.list_users.return_value = []
    users_view = UsersView(
        client, on_back=lambda: None, on_create=lambda: None, on_edit=lambda u: None
    )
    users_view.vm.refresh()
    view = users_view.build()

    joined = " | ".join(collect_text_values(view))
    assert "No hay cuentas de usuario." in joined


def test_users_view_error_state_message():
    client = MagicMock()
    client.list_users.side_effect = ApiError("No se pudo conectar con el servidor.")
    users_view = UsersView(
        client, on_back=lambda: None, on_create=lambda: None, on_edit=lambda u: None
    )
    users_view.vm.refresh()
    view = users_view.build()

    joined = " | ".join(collect_text_values(view))
    assert "No se pudo cargar la lista de cuentas." in joined


def test_users_view_edit_button_passes_user_to_callback():
    edited: list[UserOut] = []
    client = MagicMock()
    target = make_user(4, "lucia", Role.user)
    client.list_users.return_value = [target]
    users_view = UsersView(
        client, on_back=lambda: None, on_create=lambda: None, on_edit=edited.append
    )
    users_view.vm.refresh()
    view = users_view.build()

    edit_buttons = [
        n for n in walk_controls(view) if isinstance(n, ft.FilledButton) and n.content
    ]
    assert len(edit_buttons) == 1
    edit_buttons[0].on_click(None)
    assert edited == [target]


def test_users_view_back_and_new_user_buttons_wire_callbacks():
    calls: list[str] = []
    client = MagicMock()
    client.list_users.return_value = []
    users_view = UsersView(
        client,
        on_back=lambda: calls.append("back"),
        on_create=lambda: calls.append("create"),
        on_edit=lambda u: None,
    )
    view = users_view.build()

    back = [
        n
        for n in walk_controls(view)
        if isinstance(n, ft.IconButton) and n.tooltip == "Volver al catálogo"
    ]
    new_user = [
        n
        for n in walk_controls(view)
        if isinstance(n, ft.IconButton) and n.tooltip == "Nuevo usuario"
    ]
    assert len(back) == 1 and len(new_user) == 1
    back[0].on_click()
    new_user[0].on_click()
    assert calls == ["back", "create"]


# --- UserFormView structure and flows ------------------------------------------------


def test_user_form_create_mode_builds_spanish_controls():
    client = MagicMock()
    form = UserFormView(client, on_back=lambda: None, on_saved=lambda: None)
    view = form.build()

    joined = " | ".join(collect_text_values(view))
    assert "Crear usuario" in joined
    assert "Nombre de usuario" in joined
    assert "Contraseña" in joined
    assert "Rol" in joined
    assert "Guardar" in joined

    assert form._active.visible is False  # is_active is edit-only


def test_user_form_edit_mode_prefills_and_shows_switch():
    client = MagicMock()
    existing = make_user(7, "lucia", Role.admin, is_active=False)
    form = UserFormView(client, user=existing, on_back=lambda: None, on_saved=lambda: None)
    view = form.build()

    joined = " | ".join(collect_text_values(view))
    assert "Editar usuario" in joined
    assert form._username.value == "lucia"
    assert form._role.value == "admin"
    assert form._active.value is False
    assert form._active.visible is True
    assert form._password.hint_text is not None


def test_user_form_save_create_requires_password():
    client = MagicMock()
    notices: list[str] = []
    form = UserFormView(
        client,
        on_back=lambda: None,
        on_saved=lambda: notices.append("saved"),
        on_notice=notices.append,
    )
    form._username.value = "nueva"
    form._password.value = ""

    asyncio.run(form._on_save())

    client.create_user.assert_not_called()
    assert MISSING_CREDENTIALS_MESSAGE in (form._error_text.value or "")
    assert "saved" not in notices


def test_user_form_save_create_requires_username():
    client = MagicMock()
    form = UserFormView(client, on_back=lambda: None, on_saved=lambda: None)
    form._username.value = "  "
    form._password.value = "secret"

    asyncio.run(form._on_save())

    client.create_user.assert_not_called()
    assert MISSING_USERNAME_MESSAGE in (form._error_text.value or "")


def test_user_form_save_create_sends_payload_and_navigates_back():
    client = MagicMock()
    client.create_user.return_value = make_user(9, "nueva", Role.admin)
    calls: list[str] = []
    notices: list[str] = []
    form = UserFormView(
        client,
        on_back=lambda: None,
        on_saved=lambda: calls.append("saved"),
        on_notice=notices.append,
    )
    form._username.value = "nueva"
    form._password.value = "secret"
    form._role.value = "admin"

    asyncio.run(form._on_save())

    client.create_user.assert_called_once_with(
        username="nueva", password="secret", role=Role.admin
    )
    assert CREATED_MESSAGE in notices
    assert calls == ["saved"]


def test_user_form_save_edit_sends_is_active_and_notices():
    client = MagicMock()
    client.update_user.return_value = make_user(3, "ana", Role.user, is_active=True)
    notices: list[str] = []
    calls: list[str] = []
    form = UserFormView(
        client,
        user=make_user(3, "ana", Role.user, is_active=False),
        on_back=lambda: None,
        on_saved=lambda: calls.append("saved"),
        on_notice=notices.append,
    )
    form._active.value = True

    asyncio.run(form._on_save())

    kwargs = client.update_user.call_args.kwargs
    assert kwargs["is_active"] is True
    assert kwargs["role"] == Role.user
    assert USER_SAVED_MESSAGE in notices
    assert calls == ["saved"]


def test_user_form_save_api_error_shows_duplicate_message_inline():
    client = MagicMock()
    client.create_user.side_effect = ApiError("El nombre de usuario ya existe.")
    notices: list[str] = []
    form = UserFormView(
        client, on_back=lambda: None, on_saved=lambda: None, on_notice=notices.append
    )
    form._username.value = "repetida"
    form._password.value = "secret"

    asyncio.run(form._on_save())

    error = form._error_text.value or ""
    assert SAVE_ERROR_MESSAGE in error
    assert "ya existe" in error
    assert notices == []


def test_user_form_session_expired_invokes_callback():
    client = MagicMock()
    client.create_user.side_effect = AuthError("No autenticado.", status_code=401)
    expired: list[str] = []
    form = UserFormView(
        client,
        on_back=lambda: None,
        on_saved=lambda: None,
        on_session_expired=lambda: expired.append("sign-in"),
    )
    form._username.value = "x"
    form._password.value = "y"

    asyncio.run(form._on_save())

    assert expired == ["sign-in"]
