"""Catalog view: search/filter document list with per-row download (Spanish copy)."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from app.api.schemas import DocumentOut
from app.ui.api_client import ApiClient, ApiError

EMPTY_MESSAGE = "No hay documentos."
LOAD_ERROR_MESSAGE = "No se pudo cargar el catálogo."
DOWNLOAD_ERROR_MESSAGE = "No se pudo descargar el archivo."
DOWNLOAD_DONE_MESSAGE = "Archivo descargado."
DOWNLOAD_CANCELLED_MESSAGE = "Descarga cancelada."
SAVE_DIALOG_TITLE = "Guardar archivo"


class CatalogViewModel:
    """Presenter for catalog search/filter/download — pure Python, client injected."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client
        self.documents: list[DocumentOut] = []
        self.error_message: str | None = None
        self.query: str | None = None
        self.document_type: str | None = None
        self.issuing_body: str | None = None

    def refresh(self) -> None:
        try:
            self.documents = self.client.list_documents(
                query=_blank_to_none(self.query),
                document_type=_blank_to_none(self.document_type),
                issuing_body=_blank_to_none(self.issuing_body),
            )
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
    ) -> None:
        self.client = client
        self.on_sign_out = on_sign_out
        self.file_picker = file_picker
        self.on_notice = on_notice
        self.vm = CatalogViewModel(client)

        self._search_field = ft.TextField(
            label="Buscar",
            on_submit=self._on_search,
            expand=True,
        )
        self._type_field = ft.TextField(label="Tipo de documento")
        self._body_field = ft.TextField(label="Órgano emisor")
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
                ft.Row(
                    controls=[self._type_field, self._body_field],
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
                        ft.FilledButton(
                            icon=ft.Icons.DOWNLOAD,
                            content=ft.Text("Descargar"),
                            on_click=lambda _e, doc=document: self._on_download(doc),
                        ),
                    ],
                ),
            )
        )

    def _on_search(self, _event: ft.ControlEvent | None = None) -> None:
        self.vm.query = self._search_field.value
        self.vm.document_type = self._type_field.value
        self.vm.issuing_body = self._body_field.value
        self.vm.refresh()
        self._rebuild_rows()

    def _on_sign_out_click(self, _event: ft.ControlEvent | None = None) -> None:
        try:
            self.client.logout()
        except ApiError:
            pass
        self.on_sign_out()

    async def _on_download(self, document: DocumentOut) -> None:
        try:
            data = self.vm.download(document.id)
        except ApiError as exc:
            self._notice(f"{DOWNLOAD_ERROR_MESSAGE} {exc}")
            return
        filename = f"{document.title}" if document.title else "documento"
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
