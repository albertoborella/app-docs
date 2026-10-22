"""Desktop entry point for the shared Flet UI.

Run from the project root:

    DOCMANAGER_API_URL=http://127.0.0.1:8000 flet run app/ui

Flet 1.0.4 exposes ``ft.run`` (not the pre-1.0 ``ft.app`` symbol).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# `flet run app/ui` loads main.py as a script; keep the project root importable.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import flet as ft  # noqa: E402

from app.api.schemas import DocumentOut, UserOut  # noqa: E402
from app.db.models import Role  # noqa: E402
from app.ui.api_client import ApiClient  # noqa: E402
from app.ui.theme import restore_theme_mode  # noqa: E402
from app.ui.views.catalog import CatalogView  # noqa: E402
from app.ui.views.document_form import DocumentFormView  # noqa: E402
from app.ui.views.recycle_bin import RecycleBinView  # noqa: E402
from app.ui.views.sign_in import SignInView  # noqa: E402
from app.ui.views.users import UserFormView, UsersView  # noqa: E402

APP_TITLE = "Normativas Inocuidad Productos Lacteos"


def main(page: ft.Page) -> None:
    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.SYSTEM
    theme_prefs = ft.SharedPreferences()
    try:
        asyncio.create_task(restore_theme_mode(page, theme_prefs))
    except RuntimeError:
        pass  # no running loop (offline/unit usage): keep system theme
    active_catalog: dict[str, CatalogView | None] = {"catalog": None}

    def _on_page_resize(event: ft.PageResizeEvent) -> None:
        catalog_view = active_catalog["catalog"]
        if catalog_view is not None:
            catalog_view.set_viewport_width(event.width)

    page.on_resize = _on_page_resize
    client = ApiClient()
    # Flet 1.0.4: FilePicker is a Service that auto-registers with the page on
    # construction (context.page is already set inside main()). Appending it to
    # page.overlay instead renders it as an unknown visible control.
    file_picker = ft.FilePicker()
    current_user: UserOut | None = None

    def _replace(view: ft.View) -> None:
        page.views.clear()
        page.views.append(view)
        page.update()

    def _show_snack_bar(message: str) -> None:
        page.show_dialog(ft.SnackBar(ft.Text(message)))
        page.update()

    def show_sign_in() -> None:
        nonlocal current_user
        current_user = None

        def on_signed_in(user: UserOut) -> None:
            nonlocal current_user
            current_user = user
            show_catalog()

        _replace(SignInView(client, on_success=on_signed_in).build())

    def _is_admin() -> bool:
        return current_user is not None and current_user.role == Role.admin

    def show_catalog() -> None:
        catalog = CatalogView(
            client,
            on_sign_out=show_sign_in,
            file_picker=file_picker,
            on_notice=_show_snack_bar,
            web=page.web,
            is_admin=_is_admin(),
            on_new_document=lambda: show_document_form(),
            on_edit_document=show_document_form,
            on_open_recycle_bin=show_recycle_bin,
            on_open_users=show_users,
            theme_prefs=theme_prefs,
            viewport_width=page.width,
        )
        active_catalog["catalog"] = catalog
        catalog.vm.refresh()
        _replace(catalog.build())
        # Width may only be populated after the first client sync; re-check post-mount.
        catalog.set_viewport_width(page.width)

    def show_document_form(document: DocumentOut | None = None) -> None:
        form = DocumentFormView(
            client,
            document=document,
            file_picker=file_picker,
            on_back=show_catalog,
            on_saved=show_catalog,
            on_notice=_show_snack_bar,
            on_session_expired=show_sign_in,
            theme_prefs=theme_prefs,
        )
        _replace(form.build())

    def show_recycle_bin() -> None:
        view = RecycleBinView(
            client,
            on_back=show_catalog,
            on_notice=_show_snack_bar,
            on_session_expired=show_sign_in,
            theme_prefs=theme_prefs,
        )
        view.vm.refresh()
        _replace(view.build())

    def show_users() -> None:
        view = UsersView(
            client,
            on_back=show_catalog,
            on_create=lambda: show_user_form(),
            on_edit=show_user_form,
            on_notice=_show_snack_bar,
            on_session_expired=show_sign_in,
            theme_prefs=theme_prefs,
        )
        view.vm.refresh()
        _replace(view.build())

    def show_user_form(user: UserOut | None = None) -> None:
        form = UserFormView(
            client,
            user=user,
            on_back=show_users,
            on_saved=show_users,
            on_notice=_show_snack_bar,
            on_session_expired=show_sign_in,
            theme_prefs=theme_prefs,
        )
        _replace(form.build())

    show_sign_in()


if __name__ == "__main__":
    ft.run(main)
