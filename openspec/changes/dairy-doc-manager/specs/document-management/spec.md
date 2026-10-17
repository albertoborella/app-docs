# Document Management Specification

## Purpose

Catalog of official regulatory documentation for dairy-product manufacturing companies. Sources: checklist items 1-7, 10, 11, 13-15.

## Requirements

### Requirement: Shared Regulatory Document Catalog

The system SHALL maintain ONE database-backed shared catalog of official regulatory documents for dairy-product manufacturing companies. It MUST NOT be partitioned by company, tenant, or organization.

#### Scenario: Whole catalog visible

- GIVEN an authenticated normal user
- WHEN the catalog is listed
- THEN every non-deleted document is returned

### Requirement: Administrator-Only Document CRUD

Document CRUD SHALL be administrator-only: normal users MUST NOT create, update, or delete records. The administrator SHALL add documents, remove obsolete ones, and modify any stored field.

#### Scenario: Admin adds document

- GIVEN a signed-in administrator
- WHEN a new document is submitted
- THEN the record is stored and appears in the catalog

#### Scenario: Mutation refused

- GIVEN a signed-in normal user
- WHEN it attempts any create, update, or delete
- THEN the action is refused and the record is unchanged

### Requirement: Normal-User View, Search, and Filter

Normal users SHALL view the catalog, search it, and filter the list.

#### Scenario: Search works

- GIVEN a catalog containing documents
- WHEN a normal user runs a search
- THEN matching documents are returned
- AND no-match searches return empty without error

### Requirement: Soft-Delete Handling of Obsolete Documents

Removing an obsolete document SHALL be a soft delete: the record leaves the catalog for every user, stays in the database, is admin-only visible, and is restorable. Hard delete MUST NOT ship in v1; no user-visible "obsolete" state SHALL exist.

#### Scenario: Removal hides it

- GIVEN an active document
- WHEN the administrator removes it as obsolete
- THEN no listing, search, or filter returns it to normal users

#### Scenario: Admin-only visibility

- GIVEN a soft-deleted document
- WHEN the administrator opens the deleted-records view
- THEN the record is listed
- AND no normal-user view exposes it

#### Scenario: Restore

- GIVEN a soft-deleted document
- WHEN the administrator restores it
- THEN it reappears in the catalog

### Requirement: Free-Text Issuing Body

Each document record SHALL store its issuing body as admin-entered free text. No hardcoded catalog of regulators, countries, jurisdictions, or document types SHALL ship.

#### Scenario: Arbitrary value

- GIVEN an administrator entering a never-used issuing body
- WHEN the record is saved
- THEN that exact text is stored and displayed

### Requirement: Spanish User Interface (Application-Wide)

Interface copy SHALL be Spanish (neutral) on every screen (catalog, admin, sign-in). Spec prose and code identifiers stay English.

#### Scenario: Spanish copy

- GIVEN any screen
- WHEN it renders
- THEN labels, actions, and messages are Spanish (neutral)

### Requirement: Database Indexing and Search Performance

At confirmed volume (hundreds of documents, ~100 users) the database SHALL index every column used by catalog-visibility, search, and filter queries; a search-performance review SHALL be recorded before release.

#### Scenario: Queries indexed, review recorded

- GIVEN the confirmed document volume
- WHEN catalog, search, and filter queries run
- THEN every filtered column is covered by an index
- AND the review records measured timings at that volume

### Requirement: Scope Exclusions

The system SHALL NOT include: compliance checking, approvals/signatures, notifications, multi-tenancy, OCR/full-text indexing, regulator scraping, filings, analytics, separate native iOS/Android codebases (Swift or Kotlin projects distinct from the Python codebase), anonymous access, self-service features, audit exports, export/backup, hard delete.

#### Scenario: Flet mobile target is in scope

- GIVEN the fixed Flet stack (desktop, mobile, web)
- WHEN the build and packaging are inspected
- THEN the mobile target is served by the same Python codebase
- AND no separate native iOS/Android project exists

#### Scenario: Exclusions hold

- GIVEN the release
- WHEN the out-of-scope list is checked
- THEN none of those features is present

## Assumptions — Requires User Confirmation

- `ASSUMED — requires user confirmation`: document fields beyond issuing body, soft-delete marker, file link (candidates: title, description, type, dates, version, tags, URL).
- `ASSUMED — requires user confirmation`: search scope and filter dimensions (candidates: title/description text, issuing body, date range, type, tags).
- `ASSUMED — requires user confirmation`: latency target for the search-performance review; deployment target and operator (proposal-level).
