"""Catalog view: search/filter document list with per-row download (Spanish copy)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from urllib.parse import quote

import flet as ft

from app.api.schemas import DocumentOut
from app.ui.api_client import ApiClient, ApiError
from app.ui.theme import theme_toggle_button

EMPTY_MESSAGE = "No hay documentos."
LOAD_ERROR_MESSAGE = "No se pudo cargar el catálogo."
DOWNLOAD_ERROR_MESSAGE = "No se pudo descargar el archivo."
DOWNLOAD_DONE_MESSAGE = "Archivo descargado."
DOWNLOAD_CANCELLED_MESSAGE = "Descarga cancelada."
DOWNLOAD_LABEL = "Descargar"
OPEN_LABEL = "Abrir"
EDIT_LABEL = "Editar"
REMOVE_LABEL = "Quitar"
NEW_DOCUMENT_TOOLTIP = "Nuevo documento"
RECYCLE_BIN_TOOLTIP = "Papelera de reciclaje"
USERS_TOOLTIP = "Gestión de cuentas"
REMOVED_MESSAGE = "Documento retirado del catálogo."
REMOVE_ERROR_MESSAGE = "No se pudo retirar el documento."
REMOVE_DIALOG_TITLE = "Retirar documento"
REMOVE_DIALOG_QUESTION_PREFIX = "¿Retirar"
REMOVE_DIALOG_QUESTION_SUFFIX = "del catálogo?"
REMOVE_CONFIRM_LABEL = "Quitar"
REMOVE_CANCEL_LABEL = "Cancelar"
OPEN_NOTICE_MESSAGE = (
    "El documento se abrió en una pestaña nueva. "
    "Use el botón atrás del navegador o cambie de pestaña para volver al catálogo."
)
SAVE_DIALOG_TITLE = "Guardar archivo"
FILTER_DEBOUNCE_SECONDS = 0.3
MOBILE_BREAKPOINT_PX = 600


class CatalogViewModel:
    """Presenter for catalog search/filter/download — pure Python, client injected."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client
        self.documents: list[DocumentOut] = []
        self.error_message: str | None = None
        self.query: str | None = None

    def refresh(self) -> None:
        try:
            self.documents = self.client.list_documents(query=_blank_to_none(self.query))
            self.error_message = None
        except ApiError as exc:
            self.error_message = str(exc)

    def download(self, document_id: int) -> bytes:
        return self.client.download_file(document_id)

    def remove(self, document_id: int) -> None:
        self.client.delete_document(document_id)


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class CatalogView:
    """Authenticated catalog screen. Client is a constructor dependency (DI)."""

    def __init__(
        self,
        client: ApiClient,
        *,
        on_sign_out: Callable[[], None],
        file_picker: ft.FilePicker,
        on_notice: Callable[[str], None] | None = None,
        web: bool = False,
        is_admin: bool = False,
        on_new_document: Callable[[], None] | None = None,
        on_edit_document: Callable[[DocumentOut], None] | None = None,
        on_open_recycle_bin: Callable[[], None] | None = None,
        on_open_users: Callable[[], None] | None = None,
        theme_prefs: ft.SharedPreferences | None = None,
        viewport_width: float | None = None,
    ) -> None:
        self.client = client
        self.on_sign_out = on_sign_out
        self.file_picker = file_picker
        self.on_notice = on_notice
        self.web = web
        self.is_admin = is_admin
        self.on_new_document = on_new_document
        self.on_edit_document = on_edit_document
        self.on_open_recycle_bin = on_open_recycle_bin
        self.on_open_users = on_open_users
        self._theme_prefs = theme_prefs
        self._viewport_width = viewport_width
        self.vm = CatalogViewModel(client)
        self._filter_task: asyncio.Task | None = None
        self._pending_remove: DocumentOut | None = None

        self._search_field = ft.TextField(
            label="Buscar",
            hint_text="Título, tipo, organismo, país, tema o descripción",
            on_submit=self._on_search,
            on_change=self._on_filter_change,
            expand=True,
        )
        self._rows = ft.Column(spacing=8, expand=True)
        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self._empty_text = ft.Text(EMPTY_MESSAGE, visible=False)
        self._loading_ring = ft.ProgressRing(visible=False)

    def build(self) -> ft.View:
        self._rebuild_rows()
        return ft.View(
            route="/catalog",
            appbar=ft.AppBar(
                title=ft.Text("Catálogo de documentos"),
                actions=self._app_bar_actions(),
            ),
            padding=24,
            controls=[
                ft.Row(
                    controls=[
                        self._search_field,
                        ft.FilledButton(
                            content=ft.Text("Buscar"),
                            on_click=self._on_search,
                        ),
                    ]
                ),
                self._error_text,
                self._empty_text,
                self._loading_ring,
                ft.ListView(expand=True, spacing=8, controls=[self._rows]),
            ],
        )

    def _app_bar_actions(self) -> list[ft.Control]:
        actions: list[ft.Control] = []
        if self.is_admin:
            actions.extend(
                [
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        tooltip=NEW_DOCUMENT_TOOLTIP,
                        on_click=self._on_new_document_click,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        tooltip=RECYCLE_BIN_TOOLTIP,
                        on_click=self._on_recycle_bin_click,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PEOPLE,
                        tooltip=USERS_TOOLTIP,
                        on_click=self._on_users_click,
                    ),
                ]
            )
        actions.append(theme_toggle_button(self._theme_prefs))
        actions.append(
            ft.IconButton(
                icon=ft.Icons.LOGOUT,
                tooltip="Cerrar sesión",
                on_click=self._on_sign_out_click,
            )
        )
        return actions

    def _rebuild_rows(self) -> None:
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

    def _document_info(
        self, document: DocumentOut, *, expand: bool = False
    ) -> ft.Column:
        type_label = document.document_type or "—"
        date_label = document.issued_on.isoformat() if document.issued_on else "—"
        return ft.Column(
            expand=expand,
            spacing=2,
            controls=[
                ft.Text(document.title, weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"{document.issuing_body} · {type_label} · {date_label}",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
        )

    def _document_row(self, document: DocumentOut) -> ft.Control:
        if self._is_narrow():
            # Narrow (mobile): actions below the text, each button full width.
            # No expand/flex anywhere: the ListView gives unbounded height.
            return ft.Card(
                content=ft.Container(
                    padding=12,
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            self._document_info(document),
                            ft.Column(
                                spacing=8,
                                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                controls=self._row_button_list(document),
                            ),
                        ],
                    ),
                )
            )
        info = self._document_info(document, expand=True)
        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[info, self._row_actions(document)],
                ),
            )
        )

    def set_viewport_width(self, width: float | None) -> None:
        """Re-lay document rows when the viewport crosses the mobile breakpoint."""
        if width == self._viewport_width:
            return
        self._viewport_width = width
        self._rebuild_rows()
        self._push_update()

    def _is_narrow(self) -> bool:
        return (
            self._viewport_width is not None
            and self._viewport_width < MOBILE_BREAKPOINT_PX
        )

    def _row_button_list(self, document: DocumentOut) -> list[ft.Control]:
        buttons: list[ft.Control] = [self._row_button(document)]
        if self.is_admin:
            buttons.append(
                ft.FilledButton(
                    icon=ft.Icons.EDIT,
                    content=ft.Text(EDIT_LABEL),
                    on_click=functools.partial(self._on_edit_click, document),
                )
            )
            buttons.append(
                ft.FilledButton(
                    icon=ft.Icons.DELETE,
                    content=ft.Text(REMOVE_LABEL),
                    on_click=functools.partial(self._on_remove_click, document),
                )
            )
        return buttons

    def _row_actions(self, document: DocumentOut) -> ft.Control:
        return ft.Row(spacing=8, wrap=True, controls=self._row_button_list(document))

    def _row_button(self, document: DocumentOut) -> ft.FilledButton:
        if self.web:
            return ft.FilledButton(
                icon=ft.Icons.OPEN_IN_NEW,
                content=ft.Text(OPEN_LABEL),
                # Client-side open stays inside the tap gesture (iOS Safari ignores
                # window.open after a Python round trip); on_click only announces
                # how to come back once the new tab is already open.
                action=ft.OpenUrl(self._file_url(document), target=ft.UrlTarget.BLANK),
                on_click=self._on_open_click,
            )
        return ft.FilledButton(
            icon=ft.Icons.DOWNLOAD,
            content=ft.Text(DOWNLOAD_LABEL),
            on_click=functools.partial(self._on_download, document),
        )

    def _file_url(self, document: DocumentOut) -> str:
        """Browser-navigable URL for the file: query token + inline display."""
        token = quote(self.client.token or "", safe="")
        return (
            f"{self.client.base_url}/api/v1/documents/{document.id}/file"
            f"?token={token}&inline=true"
        )

    async def _on_search(self, _event: ft.ControlEvent | None = None) -> None:
        self._cancel_filter_task()
        await self._apply_filters()

    async def _on_filter_change(self, _event: ft.ControlEvent | None = None) -> None:
        self._cancel_filter_task()
        self._filter_task = asyncio.create_task(self._apply_filters_debounced())

    async def _apply_filters_debounced(self) -> None:
        try:
            await asyncio.sleep(FILTER_DEBOUNCE_SECONDS)
        except asyncio.CancelledError:
            return
        await self._apply_filters()

    def _cancel_filter_task(self) -> None:
        if self._filter_task is not None:
            self._filter_task.cancel()
            self._filter_task = None

    async def _apply_filters(self) -> None:
        self.vm.query = self._search_field.value
        self._set_loading(True)
        await asyncio.to_thread(self.vm.refresh)
        self._set_loading(False)
        self._rebuild_rows()
        self._push_update()

    def _set_loading(self, loading: bool) -> None:
        self._loading_ring.visible = loading
        self._push_update()

    def _push_update(self) -> None:
        """Push rebuilt rows to the client; no-op when offline (unit tests)."""
        try:
            page = self._rows.page
        except RuntimeError:
            return
        page.update()

    def _on_sign_out_click(self, _event: ft.ControlEvent | None = None) -> None:
        self._cancel_filter_task()
        try:
            self.client.logout()
        except ApiError:
            pass
        self.on_sign_out()

    def _on_new_document_click(self, _event: ft.ControlEvent | None = None) -> None:
        if self.on_new_document is not None:
            self.on_new_document()

    def _on_edit_click(
        self, document: DocumentOut, _event: ft.ControlEvent | None = None
    ) -> None:
        if self.on_edit_document is not None:
            self.on_edit_document(document)

    def _on_recycle_bin_click(self, _event: ft.ControlEvent | None = None) -> None:
        if self.on_open_recycle_bin is not None:
            self.on_open_recycle_bin()

    def _on_users_click(self, _event: ft.ControlEvent | None = None) -> None:
        if self.on_open_users is not None:
            self.on_open_users()

    def _on_remove_click(
        self, document: DocumentOut, _event: ft.ControlEvent | None = None
    ) -> None:
        """Stage the removal and ask for confirmation (no-op when offline)."""
        self._pending_remove = document
        try:
            page = self._rows.page
        except RuntimeError:
            return
        page.show_dialog(self._build_remove_dialog())

    def _build_remove_dialog(self) -> ft.AlertDialog:
        title = self._pending_remove.title if self._pending_remove else ""
        return ft.AlertDialog(
            modal=True,
            title=ft.Text(REMOVE_DIALOG_TITLE),
            content=ft.Text(f"{REMOVE_DIALOG_QUESTION_PREFIX} “{title}” "
                            f"{REMOVE_DIALOG_QUESTION_SUFFIX}"),
            actions=[
                ft.TextButton(
                    content=ft.Text(REMOVE_CANCEL_LABEL),
                    on_click=self._on_remove_cancel,
                ),
                ft.FilledButton(
                    icon=ft.Icons.DELETE,
                    content=ft.Text(REMOVE_CONFIRM_LABEL),
                    on_click=self._on_remove_confirm,
                ),
            ],
        )

    async def _on_remove_cancel(self, _event: ft.ControlEvent | None = None) -> None:
        self._pending_remove = None
        self._close_dialog()

    async def _on_remove_confirm(self, _event: ft.ControlEvent | None = None) -> None:
        document = self._pending_remove
        self._pending_remove = None
        self._close_dialog()
        if document is not None:
            await self._on_remove(document)

    def _close_dialog(self) -> None:
        try:
            page = self._rows.page
        except RuntimeError:
            return
        page.pop_dialog()

    async def _on_remove(
        self, document: DocumentOut, _event: ft.ControlEvent | None = None
    ) -> None:
        try:
            await asyncio.to_thread(self.vm.remove, document.id)
        except ApiError as exc:
            self._notice(f"{REMOVE_ERROR_MESSAGE} {exc}")
            return
        self._notice(REMOVED_MESSAGE)
        await self._apply_filters()

    def _on_open_click(self, _event: ft.ControlEvent | None = None) -> None:
        self._notice(OPEN_NOTICE_MESSAGE)

    async def _on_download(
        self, document: DocumentOut, _event: ft.ControlEvent | None = None
    ) -> None:
        try:
            data = await asyncio.to_thread(self.vm.download, document.id)
        except ApiError as exc:
            self._notice(f"{DOWNLOAD_ERROR_MESSAGE} {exc}")
            return
        filename = document.title or "documento"
        saved_path = await self.file_picker.save_file(
            dialog_title=SAVE_DIALOG_TITLE,
            file_name=filename,
            src_bytes=data,
        )
        if saved_path is None:
            self._notice(DOWNLOAD_CANCELLED_MESSAGE)
        else:
            self._notice(DOWNLOAD_DONE_MESSAGE)

    def _notice(self, message: str) -> None:
        if self.on_notice is not None:
            self.on_notice(message)
