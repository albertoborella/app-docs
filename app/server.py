"""Single-port entry: FastAPI API + Flet UI together (demo/deploy runs).

    uv run uvicorn app.server:app --host 127.0.0.1 --port 8080

Defaults below point the UI's server-side API calls at this same process and
make browser file links same-origin relative, so a tunnel or proxy in front of
this port needs no per-origin configuration. Override via environment when
running on a different port.
"""

import os

os.environ.setdefault("DOCMANAGER_API_URL", "http://127.0.0.1:8080")
os.environ.setdefault("DOCMANAGER_PUBLIC_API_URL", "")

from app.main import create_app  # noqa: E402

app = create_app(mount_flet=True)
