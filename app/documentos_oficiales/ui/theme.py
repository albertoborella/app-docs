"""Light/dark theme toggle shared by every AppBar, with persistence.

Flet 1.0.4 verified API: ``page.theme_mode`` accepts ``ft.ThemeMode`` values,
``control.page`` raises ``RuntimeError`` while the control is not mounted (unit
tests build views offline), and ``ft.SharedPreferences`` is a page-registered
Service with async ``get``/``set`` (browser localStorage on web).
"""

from __future__ import annotations

import flet as ft

THEME_TOGGLE_TOOLTIP = "Cambiar tema"
THEME_STORAGE_KEY = "dairy_docs.theme_mode"


def next_theme_mode(current: ft.ThemeMode | None) -> ft.ThemeMode:
    """Flip between light and dark; system counts as light for the first click."""
    if current == ft.ThemeMode.DARK:
        return ft.ThemeMode.LIGHT
    return ft.ThemeMode.DARK


def _icon_for(mode: ft.ThemeMode | None) -> ft.Icons:
    """Show the mode the next click switches TO."""
    return ft.Icons.LIGHT_MODE if mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE


def theme_toggle_button(prefs: ft.SharedPreferences | None = None) -> ft.IconButton:
    button = ft.IconButton(icon=_icon_for(None), tooltip=THEME_TOGGLE_TOOLTIP)

    async def on_click(_event: ft.ControlEvent | None = None) -> None:
        try:
            page = button.page
        except RuntimeError:
            return
        page.theme_mode = next_theme_mode(page.theme_mode)
        button.icon = _icon_for(page.theme_mode)
        page.update()
        if prefs is not None:
            try:
                await prefs.set(THEME_STORAGE_KEY, page.theme_mode.value)
            except Exception:  # noqa: BLE001 - persistence is best-effort
                pass

    button.on_click = on_click
    return button


async def restore_theme_mode(page: ft.Page, prefs: ft.SharedPreferences) -> None:
    """Apply the persisted theme at startup; keep SYSTEM when nothing stored."""
    try:
        stored = await prefs.get(THEME_STORAGE_KEY)
        if stored in ("light", "dark"):
            page.theme_mode = ft.ThemeMode(stored)
            page.update()
    except Exception:  # noqa: BLE001 - best-effort restore, never block startup
        pass
