"""Idempotent additive schema upgrades for pre-existing SQLite databases.

create_all only creates missing tables — it never ALTERs existing ones. The
create-admin CLI is the schema authority: it calls this after create_all so
user databases created before country/topic keep working.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine

DOCUMENT_OPTIONAL_COLUMNS = ("country", "topic")


def ensure_document_columns(engine: Engine) -> None:
    """Add missing optional documents columns (country/topic) via ALTER TABLE.

    Idempotent: PRAGMA table_info detects existing columns; a second run is a
    no-op. SQLite-specific on purpose (the project ships SQLite only).
    """
    with engine.begin() as conn:
        table = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        ).first()
        if table is None:
            return
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(documents)"))}
        for column in DOCUMENT_OPTIONAL_COLUMNS:
            if column not in existing:
                conn.execute(text(f"ALTER TABLE documents ADD COLUMN {column} TEXT"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_documents_country ON documents (country)")
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_documents_topic ON documents (topic)")
        )
