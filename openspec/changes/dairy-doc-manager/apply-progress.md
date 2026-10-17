# Apply Progress: dairy-doc-manager

**Batch**: Phase 1 (Foundation) — tasks 1.1–1.6 only | **Mode**: Standard (strict_tdd: false)
**Branch**: feat/dairy-doc-manager-phase-1-foundation | **Chain**: stacked-to-main (PR 1 of 8) | **Date**: 2026-10-17

## Completed Tasks

- [x] 1.1 `.gitignore` — var/, *.db, *.sqlite*, __pycache__/, *.pyc, .venv/ (+ .pytest_cache/, .ruff_cache/)
- [x] 1.2 `pyproject.toml` — pinned fastapi/uvicorn/sqlmodel/flet[web]/httpx/bcrypt/pytest/ruff; Python >= 3.10; ruff `UP` enforces PEP 604 `X | None`
- [x] 1.3 `app/core/config.py` (storage dir ./var/storage, 12h TTL), `app/db/session.py` (WAL + foreign_keys=ON), `app/db/models.py` (Role, User, UserSession, Document indexed title/issuing_body/deleted_at + partial index `ix_documents_deleted_at_active` WHERE deleted_at IS NULL, DocumentFile)
- [x] 1.4 `tests/test_security.py` → `app/core/security.py` — bcrypt (NOT passlib); 256-bit token; only SHA-256 persisted; expired TTL rejected
- [x] 1.5 `tests/test_cli_create_admin.py` — bcrypt admin on empty DB; refuses without --force; `--password` argv rejected (exit 2); getpass patched
- [x] 1.6 `app/cli.py` — argparse + getpass `create-admin` (--username optional, password always prompted, --force); Spanish operator errors

## Work Unit Evidence (Unit 1: Scaffold+CLI)

| Evidence | Value |
|---|---|
| Focused test command | `.venv/bin/python -m pytest tests/ -q` → 9 passed; `ruff check .` → All checks passed |
| Runtime harness | CLI exercised in-process via `main()` with patched getpass + temp SQLite (4 tests). HTTP harness N/A — no HTTP surface until Phase 2. |
| Rollback boundary | Remove `.gitignore`, `pyproject.toml`, `app/`, `tests/`; revert `openspec/config.yaml` + `tasks.md`. Nothing else depends on this yet. |

## Deviations

- Standalone `flet-fastapi` pin omitted: that PyPI package is stale (0.20.2 requires fastapi <0.102, conflicts). `flet.fastapi` ships inside `flet` since 0.25+; pinned `flet[web]==1.0.4` — matches design "flet (+flet.fastapi)".
- Additive env var `DOCMANAGER_DB_PATH` (default `var/app.db`) for CLI/test temp SQLite targeting.
- `openspec/config.yaml`: only stack/testing detection fields updated; `context.Architecture` line left as-is (out of scope).
- Remaining: Phases 2–8 unchanged (2.1 … 8.2). Deployment target/operator still open P0 (non-blocking).
