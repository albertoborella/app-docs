"""Admin document form: create/edit metadata, then attach file (Spanish copy)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import date

import flet as ft

from app.api.schemas import DocumentOut, FileOut
from app.ui.api_client import ApiClient, ApiError, AuthError
from app.ui.theme import theme_toggle_button

CREATE_TITLE = "Nuevo documento"
EDIT_TITLE = "Editar documento"
SAVE_LABEL = "Guardar"
UPLOAD_LABEL = "Adjuntar archivo"
BACK_TOOLTIP = "Volver al catálogo"
TITLE_LABEL = "Título"
ISSUING_BODY_LABEL = "Órgano emisor"
DESCRIPTION_LABEL = "Descripción"
DOCUMENT_TYPE_LABEL = "Tipo de documento"
COUNTRY_LABEL = "País"
TOPIC_LABEL = "Tema"
ISSUED_ON_LABEL = "Fecha de emisión"
ISSUED_ON_HINT = "AAAA-MM-DD"
MISSING_FIELDS_MESSAGE = "Complete título y órgano emisor."
INVALID_DATE_MESSAGE = "La fecha debe tener el formato AAAA-MM-DD."
SAVED_MESSAGE = "Documento guardado."
UPLOADED_MESSAGE = "Archivo adjunto."
UPLOAD_CANCELLED_MESSAGE = "Selección cancelada. El documento se guardó sin archivo."
SAVE_ERROR_MESSAGE = "No se pudo guardar el documento."
UPLOAD_ERROR_MESSAGE = "No se pudo adjuntar el archivo."
SAVE_FIRST_MESSAGE = "Guarde el documento antes de adjuntar un archivo."
PICK_FILE_TITLE = "Seleccionar archivo"


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class DocumentFormViewModel:
    """Presenter for document create/edit/upload — pure Python, client injected."""

    def __init__(self, client: ApiClient, document: DocumentOut | None = None) -> None:
        self.client = client
        self.document = document
        self.error_message: str | None = None
        self.session_expired = False

    def save(
        self,
        *,
        title: str,
        issuing_body: str,
        description: str | None = None,
        document_type: str | None = None,
        country: str | None = None,
        topic: str | None = None,
        issued_on: str | None = None,
    ) -> DocumentOut:
        try:
            if self.document is None:
                self.document = self.client.create_document(
                    title=title,
                    issuing_body=issuing_body,
                    description=description,
                    document_type=document_type,
                    country=country,
                    topic=topic,
                    issued_on=issued_on,
                )
            else:
                self.document = self.client.update_document(
                    self.document.id,
                    title=title,
                    issuing_body=issuing_body,
                    description=description,
                    document_type=document_type,
                    country=country,
                    topic=topic,
                    issued_on=issued_on,
                )
        except AuthError as exc:
            self.session_expired = True
            self.error_message = str(exc)
            raise
        except ApiError as exc:
            self.error_message = str(exc)
            raise
        self.error_message = None
        return self.document

    def upload_from_path(self, local_path: str) -> FileOut:
        return self.client.upload_file(self._require_document().id, local_path)

    def upload_from_bytes(self, filename: str, content: bytes) -> FileOut:
        return self.client.upload_file_bytes(self._require_document().id, filename, content)

    def _require_document(self) -> DocumentOut:
        if self.document is None:
            raise RuntimeError("document is required for upload")
        return self.document


class DocumentFormView:
    """Admin document form screen. Client and picker are constructor dependencies."""

    def __init__(
        self,
        client: ApiClient,
        *,
        document: DocumentOut | None = None,
        file_picker: ft.FilePicker,
        on_back: Callable[[], None],
        on_saved: Callable[[], None],
        on_notice: Callable[[str], None] | None = None,
        on_session_expired: Callable[[], None] | None = None,
        theme_prefs: ft.SharedPreferences | None = None,
    ) -> None:
        self.client = client
        self.file_picker = file_picker
        self.on_back = on_back
        self.on_saved = on_saved
        self.on_notice = on_notice
        self.on_session_expired = on_session_expired
        self._theme_prefs = theme_prefs
        self.vm = DocumentFormViewModel(client, document)

        self._title = ft.TextField(label=TITLE_LABEL, autofocus=document is None)
        self._issuing_body = ft.TextField(label=ISSUING_BODY_LABEL)
        self._description = ft.TextField(
            label=DESCRIPTION_LABEL, multiline=True, min_lines=2, max_lines=5
        )
        self._document_type = ft.TextField(label=DOCUMENT_TYPE_LABEL)
        self._country = ft.TextField(label=COUNTRY_LABEL)
        self._topic = ft.TextField(label=TOPIC_LABEL)
        self._issued_on = ft.TextField(label=ISSUED_ON_LABEL, hint_text=ISSUED_ON_HINT)
        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        if document is not None:
            self._prefill(document)

    def _prefill(self, document: DocumentOut) -> None:
        self._title.value = document.title
        self._issuing_body.value = document.issuing_body
        self._description.value = document.description
        self._document_type.value = document.document_type
        self._country.value = document.country
        self._topic.value = document.topic
        self._issued_on.value = document.issued_on.isoformat() if document.issued_on else None

    def build(self) -> ft.View:
        heading = EDIT_TITLE if self.vm.document is not None else CREATE_TITLE
        return ft.View(
            route="/admin/document-form",
            appbar=ft.AppBar(
                title=ft.Text(heading),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip=BACK_TOOLTIP,
                    on_click=self._on_back,
                ),
                actions=[theme_toggle_button(self._theme_prefs)],
            ),
            padding=24,
            controls=[
                ft.Column(
                    expand=True,
                    spacing=16,
                    controls=[
                        self._title,
                        self._issuing_body,
                        self._description,
                        self._document_type,
                        self._country,
                        self._topic,
                        self._issued_on,
                        self._error_text,
                        ft.Row(
                            wrap=True,
                            spacing=12,
                            controls=[
                                ft.FilledButton(
                                    content=ft.Text(SAVE_LABEL), on_click=self._on_save
                                ),
                                ft.FilledButton(
                                    icon=ft.Icons.UPLOAD_FILE,
                                    content=ft.Text(UPLOAD_LABEL),
                                    on_click=self._on_upload,
                                ),
                            ],
                        ),
                    ],
                )
            ],
        )

    def _on_back(self, _event: ft.ControlEvent | None = None) -> None:
        self.on_back()

    async def _on_save(self, _event: ft.ControlEvent | None = None) -> None:
        title = (self._title.value or "").strip()
        issuing_body = (self._issuing_body.value or "").strip()
        if not title or not issuing_body:
            self._show_error(MISSING_FIELDS_MESSAGE)
            return
        issued_on = _blank_to_none(self._issued_on.value)
        if issued_on is not None:
            try:
                date.fromisoformat(issued_on)
            except ValueError:
                self._show_error(INVALID_DATE_MESSAGE)
                return
        was_create = self.vm.document is None
        try:
            await asyncio.to_thread(
                self.vm.save,
                title=title,
                issuing_body=issuing_body,
                description=_blank_to_none(self._description.value),
                document_type=_blank_to_none(self._document_type.value),
                country=_blank_to_none(self._country.value),
                topic=_blank_to_none(self._topic.value),
                issued_on=issued_on,
            )
        except AuthError:
            self._handle_session_expired()
            return
        except ApiError as exc:
            self._show_error(f"{SAVE_ERROR_MESSAGE} {exc}")
            return
        self._clear_error()
        self._notice(SAVED_MESSAGE)
        if was_create:
            await self._prompt_upload()

    async def _on_upload(self, _event: ft.ControlEvent | None = None) -> None:
        await self._prompt_upload()

    async def _prompt_upload(self) -> None:
        if self.vm.document is None:
            self._notice(SAVE_FIRST_MESSAGE)
            return
        files = await self.file_picker.pick_files(
            dialog_title=PICK_FILE_TITLE, allow_multiple=False, with_data=True
        )
        if not files:
            self._notice(UPLOAD_CANCELLED_MESSAGE)
            return
        picked = files[0]
        try:
            if picked.path:
                await asyncio.to_thread(self.vm.upload_from_path, picked.path)
            else:
                await asyncio.to_thread(
                    self.vm.upload_from_bytes, picked.name, picked.bytes or b""
                )
        except AuthError:
            self._handle_session_expired()
            return
        except ApiError as exc:
            self._notice(f"{UPLOAD_ERROR_MESSAGE} {exc}")
            return
        self._notice(UPLOADED_MESSAGE)

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
