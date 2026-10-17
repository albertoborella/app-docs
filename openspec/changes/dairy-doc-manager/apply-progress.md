# Apply Progress: dairy-doc-manager

**Cumulative batches**: Phase 1 (Foundation, tasks 1.1–1.6, commit 286244a, merged to main in 81860c3) + Phase 2 (Auth & Users API, tasks 2.1–2.2) | **Mode**: Standard (strict_tdd: false; tasks mandate RED+GREEN — followed per task)
**Branch (current batch)**: feat/dairy-doc-manager-phase-2-auth-users | **Chain**: stacked-to-main (Phase 2 = PR 2 of 8) | **Date**: 2026-10-17

## Completed Tasks

### Phase 1: Foundation (batch 1)

- [x] 1.1 `.gitignore` — var/, *.db, *.sqlite*, __pycache__/, *.pyc, .venv/ (+ .pytest_cache/, .ruff_cache/)
- [x] 1.2 `pyproject.toml` — pinned fastapi/uvicorn/sqlmodel/flet[web]/httpx/bcrypt/pytest/ruff; Python >= 3.10; ruff `UP` enforces PEP 604 `X | None`
- [x] 1.3 `app/core/config.py` (storage dir ./var/storage, 12h TTL), `app/db/session.py` (WAL + foreign_keys=ON), `app/db/models.py` (Role, User, UserSession, Document indexed title/issuing_body/deleted_at + partial index `ix_documents_deleted_at_active` WHERE deleted_at IS NULL, DocumentFile)
- [x] 1.4 `tests/test_security.py` → `app/core/security.py` — bcrypt (NOT passlib); 256-bit token; only SHA-256 persisted; expired TTL rejected
- [x] 1.5 `tests/test_cli_create_admin.py` — bcrypt admin on empty DB; refuses without --force; `--password` argv rejected (exit 2); getpass patched
- [x] 1.6 `app/cli.py` — argparse + getpass `create-admin` (--username optional, password always prompted, --force); Spanish operator errors

### Phase 2: Auth & Users API (batch 2)

- [x] 2.1 RED+GREEN `tests/test_auth_api.py` (12 tests) → `app/services/auth_service.py` (authenticate/create_session/resolve_session/logout), `app/api/deps.py` (`get_current_user` via HTTPBearer, `require_admin`), `app/api/routes/auth.py` (POST /api/v1/auth/login, POST /auth/logout, GET /auth/me): token minted on login (only SHA-256 persisted), 401s Spanish ("Credenciales inválidas." / "No autenticado."), logout deletes session row, deactivated rejected on sign-in AND on in-flight token, expired token rejected
- [x] 2.2 RED+GREEN `tests/test_users_api.py` (15 tests) → `app/services/user_service.py`, `app/api/routes/users.py` (GET/POST /users, PATCH /users/{id}): admin create (201) + edit username/password/role + deactivate/reactivate; normal user 403 ("Se requiere rol de administrador."); exactly two roles (admin|user); no self-registration (no register/signup paths in OpenAPI; anon POST /users → 401); duplicate username 409; unknown user 404

## Work Unit Evidence (Unit 2: Auth+Users)

| Evidence | Value |
|---|---|
| Focused test command | `.venv/bin/python -m pytest tests/test_auth_api.py tests/test_users_api.py -q` → 27 passed; `.venv/bin/python -m pytest tests/ -q` → 36 passed (9 Phase 1 preserved); `ruff check .` → All checks passed |
| Runtime harness | uvicorn app.main:app on :8765 + curl: CLI create-admin on temp DB → login 200 mints 43-char token → GET /auth/me 200 → admin POST /users 201 → created user login 200 → normal user GET /users 403 → logout 200 → /auth/me 401. All exact results as shown. |
| Rollback boundary | Remove `app/api/`, `app/services/`, `app/main.py`, `tests/test_auth_api.py`, `tests/test_users_api.py`; revert `tasks.md` 2.1/2.2 marks + this file. Phase 1 files untouched — repo stays green on Phase 1 alone. |

Work Unit Evidence (Unit 1: Scaffold+CLI — from batch 1, preserved):

| Evidence | Value |
|---|---|
| Focused test command | `.venv/bin/python -m pytest tests/ -q` → 9 passed; `ruff check .` → All checks passed |
| Runtime harness | CLI exercised in-process via `main()` with patched getpass + temp SQLite (4 tests). HTTP harness N/A — no HTTP surface until Phase 2. |
| Rollback boundary | Remove `.gitignore`, `pyproject.toml`, `app/`, `tests/`; revert `openspec/config.yaml` + `tasks.md`. Nothing else depends on this yet. |

## TDD Cycle Evidence (tasks mandate RED+GREEN)

| Task | RED | GREEN | REFACTOR |
|---|---|---|---|
| 2.1 | `tests/test_auth_api.py` written first → collection ImportError (`app.main` absent) — RED as designed | `app/services/auth_service.py`, `app/api/deps.py`, `app/api/schemas.py`, `app/api/routes/auth.py`, minimal `app/main.py` factory → 12 passed | `UserOut` gained `ConfigDict(from_attributes=True)` (SQLModel table instances don't validate into plain BaseModel without it); `ruff format` on new files |
| 2.2 | `tests/test_users_api.py` written first → 15 failed (no /users routes) | `app/services/user_service.py`, `app/api/routes/users.py`, router wired in `main.py` → 15 passed | `ruff format` on new files; duplicate-username → 409 mapped in route via `DuplicateUsernameError` |

## Deviations

- Standalone `flet-fastapi` pin omitted (batch 1): stale on PyPI; `flet.fastapi` ships inside `flet[web]==1.0.4`.
- Additive env var `DOCMANAGER_DB_PATH` (batch 1): CLI/test temp SQLite targeting.
- `app/api/schemas.py` created (batch 2): shared request/response models (UserOut used by auth + users routes; design's Interfaces section already names UserOut). Component table listed only deps/routes — schemas module is additive, not a design change.
- `app/main.py` minimal factory created NOW (batch 2): routes need a host app; only factory + /api/v1 routers. Phase 7.1 still owns create_all-on-boot, `flet.fastapi` mount, and entry points.
- Login 401 detail is uniform "Credenciales inválidas." for wrong-password AND deactivated — avoids account-existence leak. Deactivated on in-flight token → 401 "No autenticado.".
- Duplicate username → 409 (design's error list doesn't enumerate 409; standard for uniqueness conflicts).
- PATCH ignores explicit nulls (`exclude_unset + exclude_none`); only provided non-null fields applied.
- `ruff format --check` not enforced repo-wide (Phase 1 files pre-existing unformatted); new Phase 2 files formatted individually.
- Remaining: Phases 3–8 pending (3.1 … 8.2). Deployment target/operator still open P0 (non-blocking).
