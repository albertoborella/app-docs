"""Tests for the idempotent documents schema upgrade (ensure_document_columns)."""

import sqlite3

from sqlalchemy import text

from app.db.migrations import ensure_document_columns
from app.db.session import create_db_engine

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
