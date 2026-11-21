import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    storage_dir: Path
    session_ttl: timedelta


def get_settings() -> Settings:
    return Settings(
        db_path=Path(os.environ.get("DOCMANAGER_DB_PATH", "var/app.db")),
        storage_dir=Path(os.environ.get("DOCMANAGER_STORAGE_DIR", "var/storage")),
        session_ttl=timedelta(hours=int(os.environ.get("DOCMANAGER_SESSION_TTL_HOURS", "12"))),
    )
