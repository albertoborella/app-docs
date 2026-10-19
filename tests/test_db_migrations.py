"""Tests for the idempotent documents schema upgrade (ensure_document_columns)."""

import sqlite3

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, SQLModel

from app.core.security import hash_password, utc_now
from app.db.migrations import ensure_document_columns
from app.db.models import Role, User
from app.db.session import create_db_engine
from app.main import app

OLD_DOCUMENTS_TABLE = """
CREATE TABLE documents (
    id INTEGER NOT NULL PRIMARY KEY,
    title TEXT NOT NULL,
    issuing_body TEXT NOT NULL,
    description TEXT,
    document_type TEXT,
    issued_on DATE,
    deleted_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
)
"""


def _document_columns(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return {row[1] for row in conn.execute("PRAGMA table_info(documents)")}
    finally:
        conn.close()


def _create_old_documents_table(db_path):
    engine = create_db_engine(db_path)
    with engine.begin() as conn:
        conn.execute(text(OLD_DOCUMENTS_TABLE))
    return engine


def test_ensure_document_columns_adds_missing_columns(tmp_path):
    db = tmp_path / "old.db"
    engine = _create_old_documents_table(db)

    ensure_document_columns(engine)

    assert {"country", "topic"} <= _document_columns(db)


def test_ensure_document_columns_second_run_is_noop(tmp_path):
    db = tmp_path / "old.db"
    engine = _create_old_documents_table(db)

    ensure_document_columns(engine)
    ensure_document_columns(engine)  # must not raise

    assert {"country", "topic"} <= _document_columns(db)


def test_upgraded_table_accepts_insert_and_select_with_new_columns(tmp_path):
    db = tmp_path / "old.db"
    engine = _create_old_documents_table(db)
    ensure_document_columns(engine)

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO documents (title, issuing_body, country, topic,"
                " created_at, updated_at)"
                " VALUES ('Doc', 'MVD', 'Uruguay', 'lacteos', '2024-01-01', '2024-01-01')"
            )
        )
        row = conn.execute(text("SELECT country, topic FROM documents")).one()

    assert row == ("Uruguay", "lacteos")


def test_ensure_document_columns_noop_when_table_missing(tmp_path):
    engine = create_db_engine(tmp_path / "fresh.db")  # no tables at all

    ensure_document_columns(engine)  # must not raise


def test_lifespan_heals_stale_db_and_list_documents_works(tmp_path, monkeypatch):
    """App startup upgrades a pre-existing DB; GET /documents no longer 500s."""
    db = tmp_path / "stale.db"
    engine = _create_old_documents_table(db)  # documents table WITHOUT country/topic
    SQLModel.metadata.create_all(engine)  # adds users etc.; existing documents skipped
    with Session(engine) as session:
        now = utc_now()
        session.add(
            User(
                username="admin",
                password_hash=hash_password("secret"),
                role=Role.admin,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
    engine.dispose()

    monkeypatch.setenv("DOCMANAGER_DB_PATH", str(db))

    with TestClient(app) as client:  # entering the context runs the lifespan
        login = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "secret"}
        )
        assert login.status_code == 200
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {login.json()['token']}"},
        )

    assert response.status_code == 200
    assert response.json() == []
    assert {"country", "topic"} <= _document_columns(db)
