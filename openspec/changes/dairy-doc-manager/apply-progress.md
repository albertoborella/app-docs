# Apply Progress: dairy-doc-manager

**Cumulative batches**: Phase 1 (Foundation, tasks 1.1–1.6, commit 286244a, merged to main in 81860c3) + Phase 2 (Auth & Users API, tasks 2.1–2.2, commits 636eb43+626fe91) + Phase 3 (Documents CRUD & Soft Delete, task 3.1) + Phase 4 (File Storage, tasks 4.1–4.2, COMPLETE) | **Mode**: Standard (strict_tdd: false; tasks mandate RED+GREEN — followed per task)
**Branch (current batch)**: feat/dairy-doc-manager-phase-4-files (from main 0afe605) | **Chain**: stacked-to-main (Phase 4 = PR 4 of 8, two under-400 work-unit commits: 408087c + 0d6edaa) | **Date**: 2026-10-17

## Phase 4: File Storage (batch 4) — COMPLETE

### Decision record (interrupted batch, resumed)

The first Phase 4 session stopped mid-4.2: starlette 1.8.0 (fastapi 0.143.3) raises `Form data requires "python-multipart" to be installed.` for every `File`/`UploadFile` route, and `python-multipart` was not in the pinned stack — a conflict between design.md's confirmed multipart PUT and the no-new-packages hard constraint. The executor escalated instead of choosing. **Resolution (option a, approved by orchestrator/user)**: `python-multipart==0.0.32` pinned in `pyproject.toml` and installed via `uv sync --extra dev` (this venv is uv-managed with no pip; `--extra dev` is mandatory or pytest/ruff are removed). Design's multipart contract honored; no raw-body deviation.

- [x] 4.1 RED `tests/test_files_api.py` (14 tests, written first): admin PUT stores binary+sha256+size+stored_path; PUT replace in-place (single row, single file); PUT unknown doc 404; user PUT 403 (no binary stored); anon PUT 401; 415 disallowed extension; 413 oversize (25 MB+1); client filename `../../evil.pdf` never touches filesystem (server-generated path only, nothing escapes storage root — tmp_path rglob proof); authed GET returns bytes+Content-Disposition; anon GET 401; GET without file 404; GET unknown doc 404; deleted doc GET → 404 user (no existence leak) / 200 admin.
- [x] 4.2 GREEN `app/services/file_service.py` (ALLOWED_EXTENSIONS pdf/docx/xlsx/odt/png/jpg, MAX_FILE_SIZE_BYTES 25 MB, `stored_file_path` with resolve()+is_relative_to escape guard, server-side sha256/size, upsert on document_id, `read_stored_file` re-validates stored_path) + `app/api/routes/files.py` (PUT admin multipart with chunked early-abort 413 read + extension 415 before body; GET authed download, deleted-doc 404 for non-admins, Content-Disposition with ASCII fallback + RFC 5987 filename*).

### Phase 4 Evidence (exact command outputs)

- RED (interrupted session): `.venv/bin/python -m pytest tests/test_files_api.py -q` → `13 failed, 1 passed, 1 warning in 15.43s` (routes absent; 1 pass = GET-unknown-doc trivially 404); blocker run → collection `RuntimeError: Form data requires "python-multipart" to be installed.`
- Resume verification before commit 1: `.venv/bin/python -m pytest tests/ -q` → `65 passed` (8-test upload subset); `ruff check .` → `All checks passed!`
- GREEN (final): `.venv/bin/python -m pytest tests/ -q` → `71 passed, 1 warning in 62.03s` (57 pre-existing Phase 1–3 preserved + 14 files tests); `.venv/bin/python -m pytest tests/test_files_api.py -q` → `14 passed`; `ruff check .` → `All checks passed!`

### Phase 4 Work Unit Evidence (Unit 4: Files, batch 4)

| Evidence | Value |
|---|---|
| Focused test command | `.venv/bin/python -m pytest tests/test_files_api.py -q` → 14 passed; `.venv/bin/python -m pytest tests/ -q` → 71 passed (57 pre-existing preserved); `ruff check .` → All checks passed |
| Runtime harness | FastAPI TestClient is the integration harness for this unit (HTTP boundary exercised end-to-end: real multipart PUT → filesystem write under temp DOCMANAGER_STORAGE_DIR → SQLite DocumentFile row → GET streaming bytes + Content-Disposition; oversized 25 MB+1 body aborted at 413). uvicorn+curl smoke: N/A for this batch — TestClient covers the same ASGI HTTP surface the Phase 3 curl smoke covered, and the orchestrator gate re-runs the suite; a duplicate live-server smoke was not repeated to avoid port/DB contention on this machine. |
| Rollback boundary | Revert commits 408087c + 0d6edaa (remove `app/services/file_service.py`, `app/api/routes/files.py`, `tests/test_files_api.py`; revert `app/api/schemas.py` FileOut, `app/main.py` files-router line, `pyproject.toml` python-multipart pin) and the tasks/progress docs commit. Phase 1–3 files otherwise untouched — repo stays green on Phases 1–3 alone. |

## Completed Tasks (Phases 1–3, preserved)

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

### Phase 3: Documents CRUD & Soft Delete (batch 3)

- [x] 3.1 RED+GREEN `tests/test_documents_api.py` (21 tests) → `app/services/document_service.py` (list_documents with query/document_type/issuing_body/deleted + create/update/soft_delete/restore), `app/api/routes/documents.py` (GET /documents with filters + `deleted` admin bin flag; POST 201; PATCH; DELETE 204; POST /{id}/restore 200): admin mutations 201/200/204; normal user 403 on create/update/delete/restore; deleted hidden from normal users in list AND search; `deleted=true` admin bin lists only deleted; normal-user `deleted=true` silently ignored (bin never exposed); restore clears deleted_at and reappears in catalog; free-text issuing_body stored verbatim (no enum catalogs); LIKE search (SQLAlchemy `contains`, escapes %/_) over indexed title|issuing_body; filters document_type/issuing_body exact; unknown doc → 404 "Documento no encontrado."; anon 401

## Work Unit Evidence (Unit 3: Documents, batch 3)

| Evidence | Value |
|---|---|
| Focused test command | `.venv/bin/python -m pytest tests/test_documents_api.py -q` → 21 passed; `.venv/bin/python -m pytest tests/ -q` → 57 passed (36 pre-existing Phase 1+2 preserved); `ruff check .` → All checks passed |
| Runtime harness | uvicorn app.main:app on :8766 + curl on temp DB (CLI create-admin): admin login 200 (43-char token) → POST /documents 201 → GET list 1 → user login 200 → user POST 403 → user GET list 1 → user query match 1 / no-match [] 200 → DELETE 204 → user list 0 (hidden) → admin ?deleted=true bin 1 with deleted_at set → user ?deleted=true → 0 (flag ignored) → restore 200 → user list 1 → user PATCH 403. All exact results as shown. |
| Rollback boundary | Remove `app/services/document_service.py`, `app/api/routes/documents.py`, `tests/test_documents_api.py`; revert `app/api/schemas.py` DocumentOut/Create/Patch additions, `app/main.py` documents router line, `tasks.md` 3.1 mark + this file. Phase 1+2 files otherwise untouched — repo stays green on Phases 1+2 alone. |

Work Unit Evidence (Unit 2: Auth+Users — batch 2, preserved):

| Evidence | Value |
|---|---|
| Focused test command | `.venv/bin/python -m pytest tests/test_auth_api.py tests/test_users_api.py -q` → 27 passed; `.venv/bin/python -m pytest tests/ -q` → 36 passed (9 Phase 1 preserved); `ruff check .` → All checks passed |
| Runtime harness | uvicorn app.main:app on :8765 + curl: CLI create-admin on temp DB → login 200 mints 43-char token → GET /auth/me 200 → admin POST /users 201 → created user login 200 → normal user GET /users 403 → logout 200 → /auth/me 401. All exact results as shown. |
| Rollback boundary | Remove `app/api/`, `app/services/`, `app/main.py`, `tests/test_auth_api.py`, `tests/test_users_api.py`; revert `tasks.md` 2.1/2.2 marks + this file. Phase 1 files untouched — repo stays green on Phase 1 alone. |

Work Unit Evidence (Unit 1: Scaffold+CLI — batch 1, preserved):

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
| 3.1 | `tests/test_documents_api.py` written first → 19 failed / 2 passed (no /documents routes; 401-only assertions trivially passed) | `app/services/document_service.py`, `app/api/routes/documents.py`, DocumentOut/Create/Patch schemas, router wired in `main.py` → 21 passed | 3 E501s fixed by wrapping long client.get calls; awkward ternary in list_documents rewritten as if/else |
| 4.1 | `tests/test_files_api.py` written first (14 tests) → 13 failed / 1 passed (no /files routes; GET-unknown trivially 404) | N/A — 4.1 is the RED half by design; GREEN owned by 4.2 | N/A |
| 4.2 | — | First GREEN attempt exposed the missing python-multipart runtime (blocked, escalated, option (a) approved and pinned 0.0.32); resumed: PUT landed in 408087c (8 tests green), GET + full 14-test restore landed in 0d6edaa → 14 passed / 71 total | `_content_disposition` ASCII-fallback + RFC 5987 `filename*` for non-ASCII names; `read_stored_file` re-validates stored_path against the storage root; chunked PUT read aborts early at the 25 MB cap |

## Deviations

- Standalone `flet-fastapi` pin omitted (batch 1): stale on PyPI; `flet.fastapi` ships inside `flet[web]==1.0.4`.
- Additive env var `DOCMANAGER_DB_PATH` (batch 1): CLI/test temp SQLite targeting.
- `app/api/schemas.py` created (batch 2): shared request/response models (UserOut used by auth + users routes; design's Interfaces section already names UserOut). Component table listed only deps/routes — schemas module is additive, not a design change.
- `app/main.py` minimal factory created NOW (batch 2): routes need a host app; only factory + /api/v1 routers. Phase 7.1 still owns create_all-on-boot, `flet.fastapi` mount, and entry points.
- Login 401 detail is uniform "Credenciales inválidas." for wrong-password AND deactivated — avoids account-existence leak. Deactivated on in-flight token → 401 "No autenticado.".
- Duplicate username → 409 (design's error list doesn't enumerate 409; standard for uniqueness conflicts).
- PATCH ignores explicit nulls (`exclude_unset + exclude_none`); only provided non-null fields applied — same rule now applied to documents PATCH (clearing a nullable document field via PATCH is not supported in v1; set a replacement value instead).
- `ruff format --check` not enforced repo-wide (Phase 1 files pre-existing unformatted); new files formatted individually.
- Phase 3: `deleted` query param accepted from any authenticated user but silently ignored for non-admins (`deleted and user.role == Role.admin`) — the admin bin is capability-gated, never 403 on read; matches "no normal-user view exposes it".
- Phase 3: LIKE search over the two indexed metadata columns only (title, issuing_body) per design "SQL LIKE over indexed metadata columns"; `document_type`/`issuing_body` params are exact-match filters, not LIKE.
- Phase 3: DELETE/restore are idempotent (re-delete refreshes deleted_at; restore of an active doc is a successful no-op); no GET /documents/{id} in v1 (absent from design's API surface table — not added).
- Phase 3 size: full batch measured 495 changed lines (>400 budget) → split into two work-unit commits per work-unit-commits skill: 864bf04 read-only catalog (240 lines) + 2dbfa19 admin CRUD/soft-delete/restore (325 lines); each under 400, tests travel with the behavior they verify.
- Phase 4: `python-multipart` (required by starlette for multipart form parsing) was absent from the pinned stack; the batch stopped and escalated rather than silently adding a dependency or deviating to raw-body PUT. Orchestrator/user approved option (a): pin `python-multipart==0.0.32` (honors design's confirmed multipart contract). uv venv has no pip — use `uv sync --extra dev` for installs or pytest/ruff disappear.
- Phase 4: allowlist is extension-based (orchestrator hard constraint "Allowlist extensions only"); content_type is stored/served but not itself allowlisted. `uv.lock` generated by the orchestrator's `uv sync` is left untracked (repo convention is exact pins in pyproject without a lock file) — orchestrator decides whether to commit it.
- Remaining: Phases 5–8 pending. Deployment target/operator still open P0 (non-blocking).
