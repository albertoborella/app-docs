"""Application factory. Phase 7.1 extends this with create_all and the Flet mount."""

from fastapi import FastAPI

from app.api.routes import auth, documents, files, users


def create_app() -> FastAPI:
    application = FastAPI(title="dairy-doc-manager", version="0.1.0")
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(users.router, prefix="/api/v1")
    application.include_router(documents.router, prefix="/api/v1")
    application.include_router(files.router, prefix="/api/v1")
    return application


app = create_app()
