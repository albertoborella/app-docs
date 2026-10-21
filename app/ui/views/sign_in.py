"""Sign-in view: username/password form, client.login, bootstrap hint (Spanish copy)."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from app.api.schemas import UserOut
from app.ui.api_client import ApiClient, ApiError, AuthError

BOOTSTRAP_HINT = (
    "Si es una instalación nueva y aún no existe un administrador, "
    "ejecute: python -m app.cli create-admin"
)
DEFAULT_CREDENTIALS_ERROR = "No se pudo iniciar sesión. Verifique sus credenciales."


class SignInViewModel:
    """Presenter for the sign-in form — pure Python, client injected."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client
        self.user: UserOut | None = None
        self.error_message: str | None = None
        self.bootstrap_hint: str | None = None

    def submit(self, username: str, password: str) -> bool:
        try:
            self.user = self.client.login(username, password)
        except AuthError as exc:
            self.user = None
            self.error_message = str(exc) or DEFAULT_CREDENTIALS_ERROR
            self.bootstrap_hint = BOOTSTRAP_HINT
            return False
        except ApiError as exc:
            self.user = None
            self.error_message = str(exc)
            self.bootstrap_hint = None
            return False
        self.error_message = None
        self.bootstrap_hint = None
        return True


class SignInView:
    """Sign-in screen. Client is a constructor dependency (DI)."""

    def __init__(
        self,
        client: ApiClient,
        *,
        on_success: Callable[[], None],
    ) -> None:
        self.client = client
        self.on_success = on_success
        self.vm = SignInViewModel(client)
        self._username = ft.TextField(label="Usuario", autofocus=True, autofill_hints=["username"])
        self._password = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            on_submit=self._on_submit,
            autofill_hints=["password"],
        )
        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self._hint_text = ft.Text(BOOTSTRAP_HINT, color=ft.Colors.ON_SURFACE_VARIANT, size=12)
        self._submit_button = ft.FilledButton(
            content=ft.Text("Iniciar sesión"),
            on_click=self._on_submit,
            width=280,
        )

    def build(self) -> ft.View:
        return ft.View(
            route="/sign-in",
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            padding=40,
            controls=[
                ft.Text("Documentos Inocuidad", size=22, weight=ft.FontWeight.BOLD),
                ft.Text("Inicio de sesión", size=16),
                ft.Column(
                    width=320,
                    spacing=16,
                    controls=[
                        self._username,
                        self._password,
                        self._error_text,
                        self._submit_button,
                        ft.Divider(),
                        self._hint_text,
                    ],
                ),
            ],
        )

    def _on_submit(self, _event: ft.ControlEvent | None = None) -> None:
        username = (self._username.value or "").strip()
        password = self._password.value or ""
        if not username or not password:
            self.error("Complete usuario y contraseña.")
            return
        if self.vm.submit(username, password):
            self.on_success()
            return
        self.error(self.vm.error_message or DEFAULT_CREDENTIALS_ERROR)

    def error(self, message: str) -> None:
        self._error_text.value = message
        self._error_text.visible = True
        self._hint_text.visible = True
