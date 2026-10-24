"""Application factory. Also supports mounting the Flet UI on the same port."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, documents, files, users
from app.core.config import get_settings
from app.db.migrations import ensure_document_columns
from app.db.session import create_db_engine


def create_app(*, mount_flet: bool = False) -> FastAPI:
    """Build the FastAPI app; ``mount_flet=True`` serves the UI on the same port."""

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        # Additive, idempotent schema upgrades (create-admin remains the authority
        # for creating the schema from scratch; this only heals known missing
        # columns on pre-existing databases so the API never 500s on stale DBs).
        engine = create_db_engine(get_settings().db_path)
        try:
            ensure_document_columns(engine)
        finally:
            engine.dispose()
        if mount_flet:
            import flet.fastapi as flet_fastapi

            await flet_fastapi.app_manager.start()
        yield
        if mount_flet:
            await flet_fastapi.app_manager.shutdown()

    application = FastAPI(
        title="Manejo de Documentos", version="0.1.0", lifespan=lifespan
    )
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(users.router, prefix="/api/v1")
    application.include_router(documents.router, prefix="/api/v1")
    application.include_router(files.router, prefix="/api/v1")
    if mount_flet:
        # Mounted last: the Flet app owns a catch-all index.html for its SPA.
        import flet.fastapi as flet_fastapi

        from app.ui.main import main as ui_main

        application.mount("/", flet_fastapi.app(ui_main))
    return application


app = create_app()
