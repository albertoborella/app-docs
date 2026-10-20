"""Catalog view: search/filter document list with per-row download (Spanish copy)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from urllib.parse import quote

import flet as ft

from app.api.schemas import DocumentOut
from app.ui.api_client import ApiClient, ApiError

EMPTY_MESSAGE = "No hay documentos."
LOAD_ERROR_MESSAGE = "No se pudo cargar el catálogo."
DOWNLOAD_ERROR_MESSAGE = "No se pudo descargar el archivo."
DOWNLOAD_DONE_MESSAGE = "Archivo descargado."
DOWNLOAD_CANCELLED_MESSAGE = "Descarga cancelada."
DOWNLOAD_LABEL = "Descargar"
OPEN_LABEL = "Abrir"
SAVE_DIALOG_TITLE = "Guardar archivo"
FILTER_DEBOUNCE_SECONDS = 0.3


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
    ) -> None:
        self.client = client
        self.on_sign_out = on_sign_out
        self.file_picker = file_picker
        self.on_notice = on_notice
        self.web = web
        self.vm = CatalogViewModel(client)
        self._filter_task: asyncio.Task | None = None

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

    def build(self) -> ft.View:
        self._rebuild_rows()
        return ft.View(
            route="/catalog",
            appbar=ft.AppBar(
                title=ft.Text("Catálogo de documentos"),
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        tooltip="Cerrar sesión",
                        on_click=self._on_sign_out_click,
                    )
                ],
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
                ft.ListView(expand=True, spacing=8, controls=[self._rows]),
            ],
        )

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

    def _document_row(self, document: DocumentOut) -> ft.Control:
        type_label = document.document_type or "—"
        date_label = document.issued_on.isoformat() if document.issued_on else "—"
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
                                ft.Text(
                                    document.title,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"{document.issuing_body} · {type_label} · {date_label}",
                                    size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                        ),
                        self._row_button(document),
                    ],
                ),
            )
        )

    def _row_button(self, document: DocumentOut) -> ft.FilledButton:
        if self.web:
            return ft.FilledButton(
                icon=ft.Icons.OPEN_IN_NEW,
                content=ft.Text(OPEN_LABEL),
                action=ft.OpenUrl(self._file_url(document), target=ft.UrlTarget.BLANK),
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
        await asyncio.to_thread(self.vm.refresh)
        self._rebuild_rows()
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
