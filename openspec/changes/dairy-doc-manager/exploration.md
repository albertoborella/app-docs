# Exploration: dairy-doc-manager

**Phase**: sdd-explore | **Date**: 2026-10-16 | **Artifact language**: English (neutral professional register)
**Change**: `dairy-doc-manager` | **Project**: `app-docs` at `/home/aborella/app-docs`
**Primary source**: `prompts.txt` line 2 (product brief, Spanish) — the ONLY source of product intent in this repository.
**Store mode**: both (`openspec/` files + Engram project `app-docs`)

**Confidence legend** — the single most important rule of this phase:

- `CONFIRMED` — stated directly in the product brief (or in `openspec/config.yaml` process rules).
- `ASSUMED` — inferred by this exploration for framing purposes; MUST be confirmed by the user before it becomes a requirement.

Nothing in this document is a requirement yet. No requirement may be invented downstream from an `ASSUMED` entry.

---

## 1. Problem Framing (Current State)

### What exists today (repository reality)

- `app-docs` is a **documentation-first repository with zero application code**: no package manifest, no source tree, no stack, no test runner, no linter (`openspec/config.yaml` → `context`, `testing`).
- `docs/` is a user-authored SDD scaffold of 15 `README.md` stubs. Every directory declares the documents it *expects*, but **none of the actual domain documents exist yet**:
  - `docs/vision/` expects `vision.md` (problem, users), `objectives.md`, `scope.md`, `glossary.md`.
  - `docs/requirements/` expects `business-rules.md`, `functional-requirements.md`, `non-functional-requirements.md`, `authentication.md`, `user-stories.md`.
  - `docs/domain/` expects `domain-model.md`, `entities.md`, `data-model.md`.
  - `docs/use-cases/` expects one file per use case (actor, preconditions, main flow, alternative flows).
- `docs/GLOSSARY.md` is a **generic SDD/technical glossary** — it contains no dairy, regulatory, or document-management domain terms. It cannot ground the domain model.
- `openspec/specs/` is empty: there is no consolidated main spec to delta against.
- A git repository exists (`main` @ `05535dc`, one commit) with `prompts.txt` modified — note the `sdd-init` report recorded "not a git repository"; that has since changed and is not a blocker.

### What is broken today (current-state gap)

`CONFIRMED` only at problem-statement level, from the brief:

> Dairy-product manufacturing companies must track the official documentation and requirements imposed by the official regulatory body. The brief exists because that tracking is evidently not being solved well today; the application is intended to "solve the inconveniente de gestionar la documentación oficial."

What the brief does **not** say (`ASSUMED` → needs confirmation):

- What the current manual/spreadsheet/email process actually is, and therefore what specifically fails (staleness? loss? no one knows which document is current? duplication? no search?).
- Whether obsolete documents are dangerous because they are *still being followed*, or merely because they clutter the repository. This distinction drives whether "obsolete" needs to be a **visible state** or just a deletion.
- The shape `docs/vision/` expects: one page explaining *problem → users → objectives → scope*. That page **cannot be written honestly** until the current-state process and the P0 open questions (Section 5) are answered.

### Gap summary

| Area | Today | Desired (brief) | Confidence |
| --- | --- | --- | --- |
| Document repository | Not built / unknown informal process | A database storing documents, kept current by the admin | `CONFIRMED` (destination only, not the starting pain) |
| Maintenance of documents | Unknown | Admin CRUD: add, delete obsolete, modify any field | `CONFIRMED` |
| Access by normal staff | Unknown | View, search, filter documents | `CONFIRMED` |
| Root cause of the problem | Unknown | — | unanswered, not required to start but required for `docs/vision/vision.md` |

---

## 2. Domain Concepts (candidate bounded terms)

| # | Concept | Status | Evidence / what needs confirmation |
| --- | --- | --- | --- |
| 1 | Official regulatory body ("organismo oficial regulatorio") | `CONFIRMED` | Named in the brief as the origin of the requirements. |
| 2 | Official document / requirement | `CONFIRMED` | Core object of the CRUD; brief calls them "documentación oficial, o requisitos". |
| 3 | Document record stored in a database | `CONFIRMED` | Brief: "la base de datos donde se guardan los documentos". |
| 4 | Roles: system administrator vs. normal user | `CONFIRMED` | Two roles named explicitly, with distinct capabilities. |
| 5 | Obsolete document (to be removed by admin) | `CONFIRMED` | Brief: "eliminando los obsoletos". Whether *obsolete* is a state, a flag, or just deletion → `ASSUMED`. |
| 6 | Admin CRUD (create, read, update, delete) over documents | `CONFIRMED` | Brief: "sistema de administración sencillo para hacer un crud de los documentos". |
| 7 | Normal user capabilities: view, search, filter | `CONFIRMED` | Verbatim in the brief. |
| 8 | Admin updates = add / remove obsolete / modify any field | `CONFIRMED` | Verbatim in the brief. |
| 9 | Single administrator account (or single admin at a time) | `ASSUMED` | Brief says "el administrador" (singular); user management of admins is never mentioned. |
| 10 | Document file attachment (PDF / binary) vs. metadata-only (title + link to the regulator) | `ASSUMED` | Brief never mentions files, uploads, or downloads. **Highest-impact unknown.** |
| 11 | Document fields beyond existence (title, issuing body, publication date, version, tags) | `ASSUMED` | Brief only says "algún campo de la base de datos" — generic, no field list given. |
| 12 | Document type / category | `ASSUMED` | Not named; needed to make "filter" meaningful. |
| 13 | Product line / plant / company applicability | `ASSUMED` | Brief frames the domain as "empresas productoras de productos lácteos" (plural) — may be sector framing or may imply multi-company. |
| 14 | Version / supersession (new version replaces old) | `ASSUMED` | Never mentioned; no versioning semantics exist in the brief. |
| 15 | Publication date / effective date of a document | `ASSUMED` | Never mentioned. |
| 16 | Compliance obligation / due-date tracking | `ASSUMED` | Never mentioned; the brief talks about *managing documents*, not *checking compliance*. |
| 17 | Authentication (login) for both roles | `ASSUMED` | "usuarios normales del sistema" implies accounts, but no auth is specified anywhere in the brief. |
| 18 | Audit trail (who changed what, when) | `ASSUMED` | Never mentioned. |
| 19 | Regulatory jurisdiction (which country / which body) | `ASSUMED` | Never mentioned; affects document types and language. |
| 20 | User interface language (Spanish) | `ASSUMED` | Brief is Spanish and the domain is a Spanish-speaking context; artifacts stay English regardless. |

**Rule for downstream phases**: only items 1–8 may be treated as requirements. Items 9–20 must either be answered by the user or carried explicitly as assumptions marked as such.

---

## 3. Actor & Permission Map

Stated strictly from the brief:

| Capability | System administrator | Normal user | Status |
| --- | --- | --- | --- |
| Create (add) a document | ✅ | ❌ | `CONFIRMED` |
| Read / view documents | ✅ (implied by CRUD) | ✅ | `CONFIRMED` |
| Update / modify any field of a document | ✅ | ❌ | `CONFIRMED` |
| Delete documents (specifically obsolete ones) | ✅ | ❌ | `CONFIRMED` |
| Search documents | unstated (implied ✅) | ✅ | `CONFIRMED` for normal user; admin implied |
| Filter documents | unstated (implied ✅) | ✅ | `CONFIRMED` for normal user; admin implied |
| "Keep documents current" — the admin's responsibility | ✅ | ❌ | `CONFIRMED` |
| Anything mutating | ❌ forbidden | ❌ forbidden | `CONFIRMED` (admin-only CRUD, "únicamente manejado por el administrador") |

**What the brief does NOT answer (permission gaps)**:

1. Do normal users need to log in at all, or is the catalog semi-public? (`ASSUMED`: they authenticate.)
2. Can normal users **download/open** document files, or only read metadata? Depends on Q2 (files vs. metadata).
3. Is user management (creating/disabling normal-user accounts) in scope? The brief scopes CRUD to *documents only* — account management is never mentioned.
4. Can there be **more than one** administrator?
5. Is deletion permanent, or is there a soft-delete/archive? Can an admin restore?
6. Can a document be flagged "obsolete" but retained (visible with a warning), vs. deleted outright?
7. Is there a separate admin area/UI vs. read-only user UI? (`ASSUMED`: yes — "un sistema de administración sencillo" implies a distinct admin surface.)
8. What happens on permission violation (redirect, 403, silent hide)? — implementation-level, but affects scenarios.

---

## 4. Candidate Approaches

High-level options with tradeoffs. **This is not a selection.** No approach is recommended as the decision; picking one belongs to `sdd-design` after requirements exist.

| # | Approach | Pros | Cons | Build complexity |
| --- | --- | --- | --- | --- |
| A | **Server-rendered monolithic web app** — one deployable (framework of choice) with server-side HTML, relational DB, auth and file storage handled in-process | Matches "sencillo": one codebase, one deploy, one runtime. CRUD + session auth + SQL search are the framework's bread and butter. Lowest operational surface. | Rich filtering UX is clunkier than a SPA; client interactivity limited without sprinkling JS. | Low → Medium |
| B | **API + SPA** — separate REST/GraphQL backend and a single-page frontend, DB + object storage behind the API | Clean contract between UI and data; richest search/filter UX; reusable API for future consumers (mobile, integrations). | Two deployables, CORS/token handling, duplicated validation; more architecture than a "simple admin CRUD" strictly needs. | Medium → High |
| C | **Headless CMS / off-the-shelf platform** (Strapi, Directus, Payload-style admin, or similar) configured with a `document` content type + roles | Admin CRUD, media storage, roles and editorial UI come out of the box; you configure rather than build. | Domain fit is only as good as the config; filtering/search often basic; platform lock-in and upgrade treadmill; permission model is fixed by the product. | Low (build) / Medium (fit & governance) |
| D | **No-code / low-code** (Airtable, Baserow, Notion-style base with a shared read view) | Near-zero development; instant admin CRUD; fastest path to something usable. | Weakest permission granularity, data residency/ownership questions, limited "search and filter" control, awkward to evolve into a real system; may be unacceptable for regulated-company records. | Very Low (build) / High (long-term constraints) |

**Decision drivers that are still unknown** (each one can eliminate options):

- **Files vs. metadata** (Q2): object/file storage pushes away from D and stresses C's media handling.
- **Tenancy** (Q1): multi-company kills C/D quickly and forces a real data model (A or B).
- **Deployment target & operator** (Q5): no ops capacity favors A/C/D; existing hosting may constrain the stack.
- **Volume & concurrency** (Q6): trivial volume keeps A and D viable; scale pushes to B.

---

## 5. Open Questions (prioritized)

### P0 — change the scope of the proposal; answer before `sdd-propose`

1. **Tenancy**: is this for ONE company (single-tenant) or for MULTIPLE dairy companies (multi-tenant platform)? The brief's plural "empresas productoras de productos lácteos" is ambiguous — sector framing or actual multi-company?
2. **Files vs. metadata**: does the system store the actual document files (PDF upload/download), or only metadata + a link/URL to the regulator's publication?
3. **Authentication model**: how do the admin and normal users log in? Are normal-user accounts provisioned by the admin, self-registered, or is there no login at all? Is there exactly one admin?
4. **Regulatory jurisdiction**: which country/official body(ies)? One authority or several? This shapes document types, language, and any "authority" field.
5. **Deployment target**: where must this run (company server, cloud VPS, PaaS, container)? Who operates it? Any budget/hosting constraint?
6. **Stack preference**: does the user have a preferred language/framework (or a prohibition)? No stack exists today, so this is wide open.
7. **Volume**: roughly how many documents and how many users? (Tens vs. thousands — different search and storage answers.)

### P1 — shape the feature set; answer before or during `sdd-spec`

8. What **fields** does a document record have? (title, document type, issuing body, publication/effective date, version, product line/plant applicability, tags, external URL…)
9. What does **search** mean (free-text over titles/descriptions?) and what are the **filter** dimensions (type, status, date range, product line, authority)?
10. **Delete semantics**: is "obsolete" a stored state (visible to users with a warning) or does obsolete == deleted? Permanent delete or soft delete/archive?
11. **Versioning**: when a document is replaced, does the new record supersede the old one, or is the old one simply edited in place?
12. Can normal users **download** files (if Q2 = files), or only view metadata?
13. **UI language**: Spanish for the application interface? (Artifacts stay English regardless.)

### P2 — nice to know; can default to "out of scope" if unanswered

14. Audit trail of admin changes (who modified which document, when)?
15. Notifications to users when a document changes?
16. Export/backup of the document database?
17. Full-text indexing of document *contents* (vs. metadata search only)?
18. Access for unauthenticated/public visitors?

---

## 6. Scope Boundaries (out of the first slice)

Proposed **no-go list** unless the user explicitly pulls something back in. Rationale: the brief is strictly "admin CRUD + user view/search/filter".

- ❌ Automated compliance checking, gap analysis, or obligation tracking against the regulations.
- ❌ E-signatures, approvals, or editorial review workflows.
- ❌ Notification/email workflows ("document updated" alerts).
- ❌ Multi-company / multi-tenant federation (held hostage to P0-Q1).
- ❌ OCR or full-text indexing of document contents.
- ❌ Scraping/synchronizing documents from the regulator's website.
- ❌ Regulatory filing, submission, or report generation to the authority.
- ❌ Analytics dashboards and statistics beyond a plain list/count.
- ❌ Separate native iOS/Android codebases (Swift/Kotlin projects distinct from the Python codebase).
- ❌ Anonymous/public catalog access (pending P0-Q3).
- ❌ User self-service features (password recovery flows, profiles) beyond basic login (pending P0-Q3).
- ❌ Audit-report exports and electronic invoicing/record-keeping compliance features.

> **Correction (2026-10-17, user decision)**: this list was agent-authored inference, not a user confirmation. The original entry "Native mobile applications" contradicted the user's explicit Flet desktop/mobile/web stack decision and was wrong. It has been reworded to mean only *separate* native iOS/Android codebases. The Flet mobile target — the same Python codebase rendered through the Flutter engine — is **in scope**. Downstream phases MUST NOT re-introduce a blanket mobile exclusion from this section; an explicit user decision outranks any agent-authored out-of-scope inference.

---

## Affected Areas

- `prompts.txt` — sole source of product intent (read-only input).
- `openspec/config.yaml` — rules constraining this phase, notably *"Requirements are not gathered yet; proposals MUST NOT invent requirements"*.
- `docs/vision/vision.md`, `docs/vision/scope.md` — expected documents that this exploration's answers feed (do not exist yet; `docs/` is read-only for this phase).
- `docs/requirements/*.md`, `docs/domain/*.md`, `docs/use-cases/*.md` — expected documents to be authored in later phases from confirmed answers.
- `openspec/changes/dairy-doc-manager/exploration.md` — created by this phase.
- No application code exists; no file outside `openspec/changes/dairy-doc-manager/` is modified.

## Approaches

See Section 4 (four options, tradeoffs only — no selection made by design).

## Recommendation

**Recommendation on next-phase readiness, NOT an architecture or stack choice:**

Run `sdd-propose` **only after the user answers the P0 open questions (1–7)**. A proposal written today would have to invent requirements, which `openspec/config.yaml` explicitly forbids. If the orchestrator proceeds in `interactive` mode, it should relay P0 first; the proposal must carry any still-unanswered item as an explicitly labeled assumption rather than silently converting it into a requirement.

## Risks

- The entire product intent is one paragraph; anything beyond the confirmed table (Section 2, items 1–8) is unconfirmed — **invention risk is the dominant risk of this change**.
- The files-vs-metadata decision (P0-Q2) swings architecture, effort, and two of the four candidate approaches.
- The tenancy decision (P0-Q1) swings the entire data model.
- Jurisdiction unknown (P0-Q4) → document types/authority fields cannot be named concretely.
- No stack, no test runner, no coverage tooling (`openspec/config.yaml` → `testing`): verification will be manual/documentation-based until one exists; `strict_tdd: false`.
- All `docs/` domain documents are stubs — the domain model cannot be sourced from the repository, only from user answers.
- Delivery guard context: `delivery_strategy: ask-on-risk`, `review_budget_lines: 400` — the eventual implementation is likely to exceed one 400-line PR, so `sdd-tasks` must forecast chained slices.

## Ready for Proposal

**Conditional — not yet.** The orchestrator should tell the user: exploration is complete, the confirmed core (admin-only CRUD, user view/search/filter, obsolete removal, database-backed documents) is solid, but seven P0 questions must be answered before an honest proposal can be drafted. After those answers, `sdd-propose` is the correct next phase.
