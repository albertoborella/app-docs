# Tasks: Dairy Document Manager

## Review Workload Forecast

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Work Units

| Unit | Goal | PR | Focused test | Harness | Rollback |
|------|------|----|--------------|---------|----------|
| 1 | Scaffold+CLI | 1 | pytest tests/test_security.py tests/test_cli_create_admin.py | create-admin | app/, tests/, .gitignore |
| 2 | Auth+users | 2 | pytest tests/test_auth_api.py tests/test_users_api.py | curl | services, routes, deps |
| 3 | Documents | 3 | pytest tests/test_documents_api.py | curl | document_service, routes |
| 4 | Files | 4 | pytest tests/test_files_api.py | curl | file_service, routes/files |
| 5 | Flet shared | 5 | pytest tests/test_api_client.py | flet | app/ui |
| 6 | Flet admin | 6 | pytest tests/test_ui_admin_views.py | flet | app/ui/views/admin |
| 7 | Web mount | 7 | pytest tests/test_web_mount.py | uvicorn app.main:app | main.py, pyproject |
| 8 | Perf review | 8 | pytest tests/test_performance_review.py | seed_volume.py | seed, perf-review.md |

## Phase 1: Foundation

- [x] 1.1 `.gitignore`: var/, *.db, *.sqlite*, __pycache__/, *.pyc, .venv/.
- [x] 1.2 `pyproject.toml`: pin fastapi/uvicorn/sqlmodel/flet/flet-fastapi/httpx/bcrypt/pytest/ruff; Python>=3.10; `X | None` only.
- [x] 1.3 `app/core/config.py` (storage dir, 12h TTL); `app/db/session.py` (WAL, FK ON); `app/db/models.py`: Role, User, UserSession, Document (title/issuing_body/deleted_at indexed, partial), DocumentFile.
- [x] 1.4 RED+GREEN `tests/test_security.py` → `app/core/security.py`: bcrypt not passlib; 256-bit token, SHA-256 only; expired TTL rejected.
- [x] 1.5 RED `tests/test_cli_create_admin.py`: bcrypt admin on empty DB; refuses without --force; --password argv rejected; getpass patched.
- [x] 1.6 `app/cli.py` argparse+getpass create-admin (--username optional, password prompted, --force); Spanish operator error.

## Phase 2: Auth & Users API

- [x] 2.1 RED+GREEN `tests/test_auth_api.py` → `app/services/auth_service.py`, `app/api/deps.py` (get_current_user, require_admin), `app/api/routes/auth.py`: mint token, 401s, logout deletes, deactivated rejected.
- [x] 2.2 RED+GREEN `tests/test_users_api.py` → `app/services/user_service.py`, `app/api/routes/users.py` (users list/create/patch): admin create/edit/deactivate/reactivate; user 403; two roles; no self-registration.

## Phase 3: Documents CRUD & Soft Delete

- [x] 3.1 RED+GREEN `tests/test_documents_api.py` → `app/services/document_service.py`, `app/api/routes/documents.py` (list/filters/deleted, CRUD, restore): admin 201/200; user 403; deleted hidden for users, admin bin; restore; free-text issuing_body; LIKE search.

## Phase 4: File Storage

- [x] 4.1 RED `tests/test_files_api.py`: admin PUT stores binary+sha256/size; user 403; 415; 413; GET authed; anon 401; deleted 404 user/200 admin; no path escape.
- [x] 4.2 `app/services/file_service.py` (allowlist PDF/DOCX/XLSX/ODT/PNG/JPG, 25 MB, path documents/{id}/file) + `app/api/routes/files.py` (PUT/GET); 4.1 green.

## Phase 5: Flet UI + API Client

- [x] 5.1 RED+GREEN `tests/test_api_client.py` → `app/ui/api_client.py` (httpx+bearer): login, list_documents(filters), upload_file, download_file; mocked httpx.
- [x] 5.2 Shared views: sign-in, catalog search/filter, download; Spanish; zero-admin 401 → create-admin.

## Phase 6: Admin Flet Views

- [ ] 6.1 RED+GREEN `tests/test_ui_admin_views.py` + document form, recycle bin (delete/restore), users view (create/edit/deactivate, role, password); mocked ApiClient; Spanish copy.

## Phase 7: Web Mount

- [ ] 7.1 `app/main.py`: factory, routers, create_all, flet.fastapi mount /flet-app (/ws, /upload); entries uvicorn/flet run/flet build.
- [ ] 7.2 RED+GREEN `tests/test_web_mount.py`: /flet-app responds; /api/v1 live; uvicorn smoke.

## Phase 8: Performance Review

- [ ] 8.1 `scripts/seed_volume.py` (>=300 docs, 100 users); timed queries into `openspec/changes/dairy-doc-manager/performance-review.md`.
- [ ] 8.2 Filtered columns indexed; FTS5 path if latency fails.
