import getpass
import sqlite3

import bcrypt
import pytest

from app.cli import main


@pytest.fixture
def admin_env(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DOCMANAGER_DB_PATH", str(db))
    monkeypatch.setattr(getpass, "getpass", lambda *args, **kwargs: "sup3r-s3cret")
    return db


def _admin_rows(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("select username, password_hash, role from users").fetchall()
    finally:
        conn.close()


def test_create_admin_on_empty_db_creates_bcrypt_hashed_admin(admin_env):
    assert main(["create-admin", "--username", "admin"]) == 0

    rows = _admin_rows(admin_env)
    assert len(rows) == 1
    username, password_hash, role = rows[0]
    assert username == "admin"
    assert role == "admin"
    assert bcrypt.checkpw(b"sup3r-s3cret", password_hash.encode())


def test_refuses_to_run_when_admin_exists_without_force(admin_env):
    assert main(["create-admin", "--username", "admin"]) == 0
    assert main(["create-admin", "--username", "intruso"]) == 1
    assert len(_admin_rows(admin_env)) == 1


def test_force_creates_additional_admin(admin_env):
    assert main(["create-admin", "--username", "admin"]) == 0
    assert main(["create-admin", "--username", "second", "--force"]) == 0
    assert len(_admin_rows(admin_env)) == 2


def test_password_argv_flag_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCMANAGER_DB_PATH", str(tmp_path / "test.db"))

    with pytest.raises(SystemExit) as excinfo:
        main(["create-admin", "--password", "oops-on-argv"])
    assert excinfo.value.code == 2


def test_create_admin_upgrades_old_documents_schema(admin_env):
    # Simulate a pre-upgrade database: documents table without country/topic.
    conn = sqlite3.connect(admin_env)
    try:
        conn.execute(
            """
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
        )
        conn.commit()
    finally:
        conn.close()

    assert main(["create-admin", "--username", "admin"]) == 0

    conn = sqlite3.connect(admin_env)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(documents)")}
    finally:
        conn.close()
    assert {"country", "topic"} <= columns
