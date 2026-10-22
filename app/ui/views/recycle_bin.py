"""Admin recycle bin: list soft-deleted documents, restore (Spanish copy)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from app.api.schemas import DocumentOut
from app.ui.api_client import ApiClient, ApiError, AuthError
from app.ui.theme import theme_toggle_button

TITLE = "Papelera de reciclaje"
EMPTY_MESSAGE = "No hay documentos retirados."
LOAD_ERROR_MESSAGE = "No se pudo cargar la papelera."
RESTORE_LABEL = "Restaurar"
RESTORED_MESSAGE = "Documento restaurado. Vuelve a aparecer en el catálogo."
RESTORE_ERROR_MESSAGE = "No se pudo restaurar el documento."
BACK_TOOLTIP = "Volver al catálogo"


class RecycleBinViewModel:
    """Presenter for the recycle bin — pure Python, client injected."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client
        self.documents: list[DocumentOut] = []
        self.error_message: str | None = None
        self.session_expired = False

    def refresh(self) -> None:
        try:
            self.documents = self.client.list_documents(deleted=True)
            self.error_message = None
            self.session_expired = False
        except AuthError as exc:
            self.session_expired = True
            self.error_message = str(exc)
        except ApiError as exc:
            self.error_message = str(exc)

    def restore(self, document_id: int) -> DocumentOut:
        try:
            return self.client.restore_document(document_id)
        except AuthError as exc:
            self.session_expired = True
            self.error_message = str(exc)
            raise


class RecycleBinView:
    """Admin recycle-bin screen. Client is a constructor dependency (DI)."""

    def __init__(
        self,
        client: ApiClient,
        *,
        on_back: Callable[[], None],
        on_notice: Callable[[str], None] | None = None,
        on_session_expired: Callable[[], None] | None = None,
        theme_prefs: ft.SharedPreferences | None = None,
    ) -> None:
        self.client = client
        self.on_back = on_back
        self.on_notice = on_notice
        self.on_session_expired = on_session_expired
        self._theme_prefs = theme_prefs
        self.vm = RecycleBinViewModel(client)

        self._rows = ft.Column(spacing=8, expand=True)
        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self._empty_text = ft.Text(EMPTY_MESSAGE, visible=False)

    def build(self) -> ft.View:
        self._rebuild_rows()
        return ft.View(
            route="/admin/recycle-bin",
            appbar=ft.AppBar(
                title=ft.Text(TITLE),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip=BACK_TOOLTIP,
                    on_click=self._on_back,
                ),
                actions=[theme_toggle_button(self._theme_prefs)],
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

        self._empty_text.visible = not self.vm.documents and not self.vm.error_message

        self._rows.controls.clear()
        for document in self.vm.documents:
            self._rows.controls.append(self._document_row(document))

    def _document_row(self, document: DocumentOut) -> ft.Control:
        type_label = document.document_type or "—"
        deleted_label = document.deleted_at.date().isoformat() if document.deleted_at else "—"
        subtitle = f"{document.issuing_body} · {type_label} · retirado {deleted_label}"
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
                                ft.Text(document.title, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    subtitle,
                                    size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                        ),
                        ft.FilledButton(
                            icon=ft.Icons.RESTORE,
                            content=ft.Text(RESTORE_LABEL),
                            on_click=lambda e, d=document: self._on_restore(d, e),
                        ),
                    ],
                ),
            )
        )

    def _on_back(self, _event: ft.ControlEvent | None = None) -> None:
        self.on_back()

    async def _on_restore(
        self, document: DocumentOut, _event: ft.ControlEvent | None = None
    ) -> None:
        try:
            await asyncio.to_thread(self.vm.restore, document.id)
        except AuthError:
            self._handle_session_expired()
            return
        except ApiError as exc:
            self._notice(f"{RESTORE_ERROR_MESSAGE} {exc}")
            return
        self._notice(RESTORED_MESSAGE)
        await self._reload()

    async def _reload(self) -> None:
        await asyncio.to_thread(self.vm.refresh)
        if self.vm.session_expired:
            return
        self._rebuild_rows()
        self._push_update()

    def _push_update(self) -> None:
        """Push rebuilt rows to the client; no-op when offline (unit tests)."""
        try:
            page = self._rows.page
        except RuntimeError:
            return
        page.update()

    def _handle_session_expired(self) -> None:
        if self.on_session_expired is not None:
            self.on_session_expired()

    def _notice(self, message: str) -> None:
        if self.on_notice is not None:
            self.on_notice(message)
