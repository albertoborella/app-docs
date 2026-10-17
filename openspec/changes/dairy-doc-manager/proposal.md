# Proposal: dairy-doc-manager

## Intent

Official regulatory documents in dairy manufacturing are tracked informally (`prompts.txt` L2). Deliver a shared catalog: admin-only document CRUD, user view/search/filter, file storage, admin-provisioned accounts.

## Scope

### In Scope

- Document CRUD — admin-only; normal users view, search, filter (`CONFIRMED`).
- File storage: admin uploads PDFs/docs; system stores and serves them (`CONFIRMED`, P0).
- **Scope addition (explicit)**: admin manages user accounts — create, edit, deactivate (P0: nobody self-registers); not in brief.
- Two roles, login, single shared catalog, no tenancy (`CONFIRMED`, P0).
- Free-text issuing body; no hardcoded jurisdiction values (`CONFIRMED`, P0).

### Out of Scope

Exploration §6 stands, with one user-corrected entry: compliance checking, approvals/signatures, notifications, multi-tenancy, OCR/full-text indexing, regulator scraping, filings, analytics, **separate native iOS/Android codebases**, anonymous access, self-service features, audit exports. Flet mobile is IN SCOPE — it is the same Python codebase, not a second native project.

## Capabilities

### New Capabilities

- `document-management`: admin CRUD, obsolete handling, user view/search/filter, shared catalog.
- `document-file-storage`: upload, binary storage, serving of files.
- `user-account-management`: admin-provisioned accounts, two roles, authentication.

### Modified Capabilities

None — `openspec/specs/` is empty.

## Approach

Fixed stack: FastAPI + SQLModel, SQLite3, Flet (desktop/mobile/web), PEP 604 `X | None`.

**Open design question (sdd-design)**: web may mount Flet into FastAPI via `flet.fastapi` (one deployable, `/ws`, `/upload`); desktop/mobile run native over HTTP. Recent API — pin versions.

## Assumptions — requires user confirmation

- `ASSUMED — requires user confirmation`: volume (documents, users); deployment target and operator.
- `ASSUMED — requires user confirmation` (P1 → sdd-spec): document fields; search/filter dimensions; obsolete as state vs. deletion (soft/hard, restore); versioning; normal-user download (likely; assumed); UI language.

## Proposal question round

Before spec: obsolete = state or deletion? Normal-user download? Soft/hard delete? UI language? Out-of-scope pull-backs?

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `openspec/changes/dairy-doc-manager/` | New | proposal, specs, design, tasks |
| `openspec/config.yaml` | Later | re-run stack/test detection |
| application source | New | first code in repo |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Requirement invention past the 10 confirmed | Med | Labels enforced; spec rejects unlabeled |
| `flet.fastapi` API churn | Med | Version pin; design spike |
| 400-line budget exceeded | High | sdd-tasks forecasts chained PRs |

## Rollback Plan

Pre-apply: revert change-folder files; no code/data exists, `docs/` untouched. During apply: feature branches; discard unreleased slices; revert merged slices in reverse order. Database and files ship with release.

## Dependencies

Python ≥ 3.10; FastAPI/SQLModel/SQLite3; Flet `flet.fastapi` pin TBD.

## Success Criteria

- [ ] 10 confirmed items covered; zero unconfirmed promoted to requirements.
- [ ] Every open item labeled `ASSUMED — requires user confirmation`.
- [ ] Account-management scope addition visible; deployment shape left open for design.
- [ ] Artifact identical in `openspec/` and Engram.
