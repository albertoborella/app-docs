"""Application factory. Phase 7.1 extends this with create_all and the Flet mount."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, documents, files, users
from app.core.config import get_settings
from app.db.migrations import ensure_document_columns
from app.db.session import create_db_engine


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
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Manejo de Documentos", version="0.1.0", lifespan=lifespan
    )
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(users.router, prefix="/api/v1")
    application.include_router(documents.router, prefix="/api/v1")
    application.include_router(files.router, prefix="/api/v1")
    return application


app = create_app()
