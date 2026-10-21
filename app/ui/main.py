"""Desktop entry point for the shared Flet UI.

Run from the project root:

    DOCMANAGER_API_URL=http://127.0.0.1:8000 flet run app/ui

Flet 1.0.4 exposes ``ft.run`` (not the pre-1.0 ``ft.app`` symbol).
"""

from __future__ import annotations

import sys
from pathlib import Path

# `flet run app/ui` loads main.py as a script; keep the project root importable.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import flet as ft  # noqa: E402

from app.ui.api_client import ApiClient  # noqa: E402
from app.ui.views.catalog import CatalogView  # noqa: E402
from app.ui.views.sign_in import SignInView  # noqa: E402

APP_TITLE = "Normativas Inocuidad Productos Lacteos"


def main(page: ft.Page) -> None:
    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.SYSTEM
    client = ApiClient()
    # Flet 1.0.4: FilePicker is a Service that auto-registers with the page on
    # construction (context.page is already set inside main()). Appending it to
    # page.overlay instead renders it as an unknown visible control.
    file_picker = ft.FilePicker()

    def show_sign_in() -> None:
        view = SignInView(client, on_success=show_catalog)
        page.views.clear()
        page.views.append(view.build())
        page.update()

    def show_catalog() -> None:
        catalog = CatalogView(
            client,
            on_sign_out=show_sign_in,
            file_picker=file_picker,
            on_notice=_show_snack_bar,
            web=page.web,
        )
        catalog.vm.refresh()
        page.views.clear()
        page.views.append(catalog.build())
        page.update()

    def _show_snack_bar(message: str) -> None:
        page.show_dialog(ft.SnackBar(ft.Text(message)))
        page.update()

    show_sign_in()


if __name__ == "__main__":
    ft.run(main)
