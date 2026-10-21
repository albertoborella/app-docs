"""Admin account management: list, create, edit users (Spanish copy)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from app.api.schemas import UserOut
from app.db.models import Role
from app.ui.api_client import ApiClient, ApiError, AuthError

LIST_TITLE = "Gestión de cuentas"
NEW_USER_TOOLTIP = "Nuevo usuario"
EDIT_LABEL = "Editar"
SAVE_LABEL = "Guardar"
BACK_TOOLTIP = "Volver al catálogo"
EMPTY_MESSAGE = "No hay cuentas de usuario."
LOAD_ERROR_MESSAGE = "No se pudo cargar la lista de cuentas."
CREATE_FORM_TITLE = "Crear usuario"
EDIT_FORM_TITLE = "Editar usuario"
USERNAME_LABEL = "Nombre de usuario"
PASSWORD_LABEL = "Contraseña"
PASSWORD_EDIT_HINT = "Dejar en blanco para no cambiar la contraseña"
ROLE_LABEL = "Rol"
ROLE_ADMIN_LABEL = "Administrador"
ROLE_USER_LABEL = "Usuario normal"
ACTIVE_LABEL = "Activo"
ACTIVE_STATE = "Activo"
INACTIVE_STATE = "Inactivo"
MISSING_USERNAME_MESSAGE = "Complete el nombre de usuario."
MISSING_CREDENTIALS_MESSAGE = "Complete nombre de usuario y contraseña."
CREATED_MESSAGE = "Cuenta creada."
SAVED_MESSAGE = "Cambios guardados."
SAVE_ERROR_MESSAGE = "No se pudo guardar la cuenta."

ROLE_LABELS: dict[Role, str] = {
    Role.admin: ROLE_ADMIN_LABEL,
    Role.user: ROLE_USER_LABEL,
}


def role_label(role: Role) -> str:
    return ROLE_LABELS.get(role, str(role))


class UsersViewModel:
    """Presenter for account listing — pure Python, client injected."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client
        self.users: list[UserOut] = []
        self.error_message: str | None = None
        self.session_expired = False

    def refresh(self) -> None:
        try:
            self.users = self.client.list_users()
            self.error_message = None
            self.session_expired = False
        except AuthError as exc:
            self.session_expired = True
            self.error_message = str(exc)
        except ApiError as exc:
            self.error_message = str(exc)


class UserFormViewModel:
    """Presenter for account create/edit — pure Python, client injected."""

    def __init__(self, client: ApiClient, user: UserOut | None = None) -> None:
        self.client = client
        self.user = user
        self.error_message: str | None = None
        self.session_expired = False

    def save(
        self,
        *,
        username: str,
        password: str | None,
        role: Role,
        is_active: bool,
    ) -> UserOut:
        try:
            if self.user is None:
                self.user = self.client.create_user(
                    username=username,
                    password=password or "",
                    role=role,
                )
            else:
                self.user = self.client.update_user(
                    self.user.id,
                    username=username,
                    password=password,
                    role=role,
                    is_active=is_active,
                )
        except AuthError as exc:
            self.session_expired = True
            self.error_message = str(exc)
            raise
        except ApiError as exc:
            self.error_message = str(exc)
            raise
        self.error_message = None
        return self.user


class UsersView:
    """Admin account list screen. Client is a constructor dependency (DI)."""

    def __init__(
        self,
        client: ApiClient,
        *,
        on_back: Callable[[], None],
        on_create: Callable[[], None],
        on_edit: Callable[[UserOut], None],
        on_notice: Callable[[str], None] | None = None,
        on_session_expired: Callable[[], None] | None = None,
    ) -> None:
        self.client = client
        self.on_back = on_back
        self.on_create = on_create
        self.on_edit = on_edit
        self.on_notice = on_notice
        self.on_session_expired = on_session_expired
        self.vm = UsersViewModel(client)

        self._rows = ft.Column(spacing=8, expand=True)
        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self._empty_text = ft.Text(EMPTY_MESSAGE, visible=False)

    def build(self) -> ft.View:
        self._rebuild_rows()
        return ft.View(
            route="/admin/users",
            appbar=ft.AppBar(
                title=ft.Text(LIST_TITLE),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip=BACK_TOOLTIP,
                    on_click=self._on_back,
                ),
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.PERSON_ADD,
                        tooltip=NEW_USER_TOOLTIP,
                        on_click=self._on_create,
                    )
                ],
            ),
            padding=24,
            controls=[
                self._error_text,
                self._empty_text,
                ft.ListView(expand=True, spacing=8, controls=[self._rows]),
            ],
        )

    def _rebuild_rows(self) -> None:
        if self.vm.session_expired:
            self._handle_session_expired()
        if self.vm.error_message:
            self._error_text.value = f"{LOAD_ERROR_MESSAGE} {self.vm.error_message}"
            self._error_text.visible = True
        else:
            self._error_text.value = ""
            self._error_text.visible = False

        self._empty_text.visible = not self.vm.users and not self.vm.error_message

        self._rows.controls.clear()
        for user in self.vm.users:
            self._rows.controls.append(self._user_row(user))

    def _user_row(self, user: UserOut) -> ft.Control:
        state_label = ACTIVE_STATE if user.is_active else INACTIVE_STATE
        subtitle = f"{role_label(user.role)} · {state_label}"
        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(user.username, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    subtitle,
                                    size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                        ),
                        ft.FilledButton(
                            icon=ft.Icons.EDIT,
                            content=ft.Text(EDIT_LABEL),
                            on_click=lambda e, u=user: self._on_edit_click(u, e),
                        ),
                    ],
                ),
            )
        )

    def _on_back(self, _event: ft.ControlEvent | None = None) -> None:
        self.on_back()

    def _on_create(self, _event: ft.ControlEvent | None = None) -> None:
        self.on_create()

    def _on_edit_click(self, user: UserOut, _event: ft.ControlEvent | None = None) -> None:
        self.on_edit(user)


class UserFormView:
    """Admin account create/edit screen. Client is a constructor dependency."""

    def __init__(
        self,
        client: ApiClient,
        *,
        user: UserOut | None = None,
        on_back: Callable[[], None],
        on_saved: Callable[[], None],
        on_notice: Callable[[str], None] | None = None,
        on_session_expired: Callable[[], None] | None = None,
    ) -> None:
        self.client = client
        self.on_back = on_back
        self.on_saved = on_saved
        self.on_notice = on_notice
        self.on_session_expired = on_session_expired
        self.vm = UserFormViewModel(client, user)

        self._username = ft.TextField(label=USERNAME_LABEL, autofocus=user is None)
        self._password = ft.TextField(
            label=PASSWORD_LABEL,
            password=True,
            can_reveal_password=True,
            hint_text=PASSWORD_EDIT_HINT if user is not None else None,
        )
        self._role = ft.Dropdown(
            label=ROLE_LABEL,
            value=Role.user.value,
            options=[
                ft.DropdownOption(key=Role.admin.value, text=ROLE_ADMIN_LABEL),
                ft.DropdownOption(key=Role.user.value, text=ROLE_USER_LABEL),
            ],
        )
        self._active = ft.Switch(label=ACTIVE_LABEL, value=True, visible=user is not None)
        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        if user is not None:
            self._username.value = user.username
            self._role.value = user.role.value
            self._active.value = user.is_active

    def build(self) -> ft.View:
        heading = EDIT_FORM_TITLE if self.vm.user is not None else CREATE_FORM_TITLE
        return ft.View(
            route="/admin/user-form",
            appbar=ft.AppBar(
                title=ft.Text(heading),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip=BACK_TOOLTIP,
                    on_click=self._on_back,
                ),
            ),
            padding=24,
            controls=[
                ft.Column(
                    expand=True,
                    spacing=16,
                    controls=[
                        self._username,
                        self._password,
                        self._role,
                        self._active,
                        self._error_text,
                        ft.FilledButton(content=ft.Text(SAVE_LABEL), on_click=self._on_save),
                    ],
                )
            ],
        )

    def _on_back(self, _event: ft.ControlEvent | None = None) -> None:
        self.on_back()

    async def _on_save(self, _event: ft.ControlEvent | None = None) -> None:
        username = (self._username.value or "").strip()
        password = self._password.value or ""
        is_create = self.vm.user is None
        if not username:
            self._show_error(MISSING_USERNAME_MESSAGE)
            return
        if is_create and not password:
            self._show_error(MISSING_CREDENTIALS_MESSAGE)
            return
        role = Role(self._role.value or Role.user.value)
        is_active = bool(self._active.value)
        try:
            await asyncio.to_thread(
                self.vm.save,
                username=username,
                password=password or None,
                role=role,
                is_active=is_active,
            )
        except AuthError:
            self._handle_session_expired()
            return
        except ApiError as exc:
            self._show_error(f"{SAVE_ERROR_MESSAGE} {exc}")
            return
        self._clear_error()
        self._notice(CREATED_MESSAGE if is_create else SAVED_MESSAGE)
        self.on_saved()

    def _show_error(self, message: str) -> None:
        self._error_text.value = message
        self._error_text.visible = True

    def _clear_error(self) -> None:
        self._error_text.value = ""
        self._error_text.visible = False

    def _handle_session_expired(self) -> None:
        if self.on_session_expired is not None:
            self.on_session_expired()

    def _notice(self, message: str) -> None:
        if self.on_notice is not None:
            self.on_notice(message)
