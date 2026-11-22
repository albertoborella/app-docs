"""Idempotent additive schema upgrades for pre-existing SQLite databases.

create_all only creates missing tables — it never ALTERs existing ones. The
create-admin CLI is the schema authority: it calls this after create_all so
user databases created before country/topic keep working.

Also provides CloroRegistro table creation with idempotent ALTER/TABLE IF NOT
EXISTS for the registros-cloro module.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine

DOCUMENT_OPTIONAL_COLUMNS = ("country", "topic")
CLORO_OPTIONAL_COLUMNS = ()


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


def ensure_cloro_registro_table(engine: Engine) -> None:
    """Create CloroRegistro table and indexes idempotentemente.

    Uses CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS so multiple
    runs are no-ops. SQLite-specific on purpose (the project ships SQLite only).
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """CREATE TABLE IF NOT EXISTS cloro_registro (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    cloro_ppm REAL NOT NULL,
                    temperatura_c REAL,
                    ph REAL,
                    agua_temperatura_c REAL,
                    estado TEXT NOT NULL,
                    evidencia_url TEXT,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )"""
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_cloro_user_ts ON cloro_registro (user_id, timestamp)")
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_cloro_estado ON cloro_registro (estado)")
        )
