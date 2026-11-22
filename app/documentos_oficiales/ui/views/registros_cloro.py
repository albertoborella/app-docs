"""Quick cloro registro ingestion view for mobile (Flet).

Following the pattern of existing vistas (document_form.py) and using
api_client.py existente para llamadas HTTP al API FastAPI.
"""

from __future__ import annotations

import asyncio

import flet as ft

from app.documentos_oficiales.ui.api_client import ApiClient, ApiError, AuthError
from datetime import datetime, timezone
from app.documentos_oficiales.ui.theme import theme_toggle_button


class QuickCloroFormViewModel:
    """Presenter for quick cloro form — pure Python, client injected."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client
        self.error_message: str | None = None
        self.session_expired = False

    def save(self, *, cloro_ppm: float, temperatura_c: float | None = None,
             ph: float | None = None, agua_temperatura_c: float | None = None,
             notes: str | None = None) -> dict:
        """POST /api/v1/registros-cloro y devuelve el registro creado."""
        data = self.client.create_registro_cloro(
            cloro_ppm=cloro_ppm,
            temperatura_c=temperatura_c,
            ph=ph,
            agua_temperatura_c=agua_temperatura_c,
            notes=notes,
        )
        return data


class QuickCloroFormView:
    """Quick form screen for mobile cloro registro ingestion (~30s per measurement)."""

    def __init__(
        self,
        client: ApiClient,
        *,
        theme_prefs: ft.SharedPreferences | None = None,
        on_back: callable | None = None,
        on_saved: callable | None = None,
        on_notice: callable | None = None,
        on_session_expired: callable | None = None,
    ) -> None:
        self.client = client
        self.on_back = on_back
        self.on_saved = on_saved
        self.on_notice = on_notice
        self.on_session_expired = on_session_expired
        self._theme_prefs = theme_prefs

        # Form fields — consistent with existing vistas patterns
        self._cloro_ppm = ft.TextField(
            label="Cloro (ppm)",
            hint_text="Ej: 0.3 - 1.2",
            width=200,
            border=ft.InputBorder.UNDERLINE,
            autofocus=True,
        )
        self._temperatura_c = ft.TextField(
            label="Temperatura (°C)",
            hint_text="Opcional",
            width=200,
            border=ft.InputBorder.UNDERLINE,
        )
        self._pH = ft.TextField(
            label="pH",
            hint_text="Opcional",
            width=200,
            border=ft.InputBorder.UNDERLINE,
        )
        self._agua_temperatura_c = ft.TextField(
            label="Agua Temp (°C)",
            hint_text="Opcional",
            width=200,
            border=ft.InputBorder.UNDERLINE,
        )
        self._notes = ft.TextField(
            label="Notas",
            hint_text="Opcional",
            multiline=True,
            min_lines=1,
            max_lines=2,
            width=200,
        )

        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self._success_text = ft.Text("", color=ft.Colors.GREEN, visible=False)

    def _mostrar_error(self, mensaje: str) -> None:
        self._error_text.value = mensaje
        self._error_text.visible = True
        self._success_text.visible = False

    def _limpiar_error(self) -> None:
        self._error_text.value = ""
        self._error_text.visible = False

    def _mostrar_exito(self, mensaje: str) -> None:
        self._success_text.value = mensaje
        self._success_text.visible = True
        self._error_text.visible = False

    def _validar_cliente(self) -> bool:
        """Client-side validation: cloro_ppm must be present and valid."""
        cloro_valor = self._cloro_ppm.value.strip() if self._cloro_ppm.value else ""
        if not cloro_valor:
            self._mostrar_error("El campo cloro_ppm es obligatorio.")
            return False
        try:
            val = float(cloro_valor)
            if val <= 0 or val > 10:
                self._mostrar_error("cloro_ppm debe ser > 0 y ≤ 10.")
                return False
        except ValueError:
            self._mostrar_error("cloro_ppm debe ser un número válido.")
            return False
        self._limpiar_error()
        return True

    def build(self) -> ft.View:
        """Build the Flet view with consistent theme and structure."""
        return ft.View(
            route="/registros-cloro",
            appbar=ft.AppBar(
                title=ft.Text("Registro de Cloro"),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Volver",
                    on_click=lambda _: self.on_back() if self.on_back else None,
                ),
                actions=[theme_toggle_button(self._theme_prefs)],
            ),
            padding=20,
            controls=[
                ft.Column(
                    spacing=12,
                    controls=[
                        self._cloro_ppm,
                        self._temperatura_c,
                        self._pH,
                        self._agua_temperatura_c,
                        self._notes,
                        self._error_text,
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.FilledButton(
                                    text="ENVIAR",
                                    on_click=lambda _: self._on_enviar(),
                                ),
                                ft.OutlinedButton(
                                    text="CANCELAR",
                                    on_click=lambda _: self.on_back() if self.on_back else None,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    async def _on_enviar(self, _event: ft.ControlEvent | None = None) -> None:
        """Handle ENVIAR button click with client-side validation."""
        if not self._validar_cliente():
            return

        cloro_valor = float(self._cloro_ppm.value!.strip())

        try:
            await asyncio.to_thread(
                self.vm.save,
                cloro_ppm=cloro_valor,
                temperatura_c=(
                    float(self._temperatura_c.value) if self._temperatura_c.value else None
                ),
                ph=(
                    float(self._pH.value) if self._pH.value else None
                ),
                agua_temperatura_c=(
                    float(self._agua_temperatura_c.value)
                    if self._agua_temperatura_c.value
                    else None
                ),
                notes=self._notes.value or None,
            )
        except AuthError:
            self._handle_session_expired()
            return
        except ApiError as exc:
            self._mostrar_error(f"Error al guardar: {exc}")
            return

        self._mostrar_exito("Registro guardado correctamente.")
        if self.on_saved:
            await self.on_saved()

    def _handle_session_expired(self) -> None:
        if self.on_session_expired is not None:
            self.on_session_expired()


class CloroListadoView:
    """Listado de cloro registros con filtros y evidencia display."""

    def __init__(
        self,
        client: ApiClient,
        *,
        theme_prefs: ft.SharedPreferences | None = None,
        on_back: callable | None = None,
        on_notice: callable | None = None,
    ) -> None:
        self.client = client
        self.on_back = on_back
        self.on_notice = on_notice
        self._error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self._tabla = ft.Column(spacing=4)
        self._actualizar_listado()

    def _actualizar_listado(self) -> None:
        """Fetch registros from API with current filters."""
        try:
            params: dict[str, str] = {}
            if self._get_fecha_desde():
                params["fecha_desde"] = self._get_fecha_desde()
            if self._get_fecha_hasta():
                params["fecha_hasta"] = self._get_fecha_hasta()
            if self._get_usuario_id():
                params["usuario_id"] = self._get_usuario_id()
            if self._get_estado():
                params["estado"] = self._get_estado()
            if self._get_cloro_min():
                params["cloro_min"] = self._get_cloro_min()
            if self._get_cloro_max():
                params["cloro_max"] = self._get_cloro_max()

data = self.client.listar_registros_cloro(
                fecha_desde=self._get_fecha_desde(),
                fecha_hasta=self._get_fecha_hasta(),
                usuario_id=self._get_usuario_id(),
                estado=self._get_estado(),
                cloro_min=self._get_cloro_min(),
                cloro_max=self._get_cloro_max(),
            )
            registros = data if isinstance(data, list) else []
        except (AuthError, ApiError) as exc:
            registros = []
            self._mostrar_error(f"Error cargando listado: {exc}")

        tarjetas = []
        for reg in registros:
            tarjetas.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    title=ft.Text(f"ID: {reg.get('id', 'N/A')}"),
                                    subtitle=ft.Text(
                                        f"Cloro: {reg.get('cloro_ppm', 'N/A')} ppm | "
                                        f"Estado: {reg.get('estado', 'N/A')} | "
                                        f"Fecha: {reg.get('timestamp', 'N/A')}"
                                    ),
                                ),
                                ft.Divider(),
                                ft.Row(
                                    [
                                        ft.Text(f"Evidencia: {reg.get('evidencia_url', '—')}"),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=10,
                    ),
                    margin=ft.Margin(4, 4, 4, 4),
                )
            )

        self._tabla.controls = tarjetas
        self.update()

    def _get_fecha_desde(self) -> str | None:
        return self._fecha_desde.value.strip() if self._fecha_desde.value else None

    def _get_fecha_hasta(self) -> str | None:
        return self._fecha_hasta.value.strip() if self._fecha_hasta.value else None

    def _get_usuario_id(self) -> int | None:
        v = self._usuario_id.value.strip() if self._usuario_id.value else None
        return int(v) if v else None

    def _get_estado(self) -> str | None:
        return self._estado.value.strip() if self._estado.value else None

    def _get_cloro_min(self) -> float | None:
        v = self._cloro_min.value.strip() if self._cloro_min.value else None
        return float(v) if v else None

    def _get_cloro_max(self) -> float | None:
        v = self._cloro_max.value.strip() if self._cloro_max.value else None
        return float(v) if v else None

    def build(self) -> ft.View:
        """Build the listado view with filters and table."""
        return ft.View(
            route="/registros-cloro/listado",
            appbar=ft.AppBar(
                title=ft.Text("Historial de Registros Cloro"),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Volver",
                    on_click=lambda _: self.on_back() if self.on_back else None,
                ),
                actions=[theme_toggle_button(self._theme_prefs)],
            ),
            padding=20,
            controls=[
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            spacing=12,
                            controls=[
                                self._fecha_desde,
                                self._fecha_hasta,
                                self._usuario_id,
                                self._estado,
                                self._cloro_min,
                                self._cloro_max,
                            ],
                        ),
                        ft.FilledButton(
                            text="APLICAR FILTROS",
                            on_click=lambda _: self._actualizar_listado(),
                        ),
                        self._error_text,
                        self._tabla,
                    ],
                ),
            ],
        )

    def _handle_session_expired(self) -> None:
        if hasattr(self, 'on_session_expired') and self.on_session_expired is not None:
            self.on_session_expired()