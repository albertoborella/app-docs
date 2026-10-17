# Document File Storage Specification

## Purpose

Real file storage for the shared catalog: the administrator uploads document files, the system stores the binaries, and authenticated users — including normal users — are served and may download them. UI language requirement lives in `document-management` (Spanish, application-wide). Confirmed sources: enforcement checklist items 8, 12, 14, 15.

## Requirements

### Requirement: Administrator Upload and Binary Storage

The system SHALL store the actual binary of each uploaded document file (PDF and other document formats). Upload, attachment, and replacement of files SHALL be restricted to the administrator; normal users MUST NOT upload. Storing the file SHALL make it available through the document record it belongs to.

#### Scenario: Administrator uploads a PDF

- GIVEN a signed-in administrator uploading a file for a document
- WHEN the upload completes
- THEN the binary is stored and associated with that document record

#### Scenario: Normal user cannot upload

- GIVEN a signed-in normal user
- WHEN an upload or file replacement is attempted
- THEN the attempt is refused
- AND no binary is stored

### Requirement: File Serving to Authenticated Users

The system SHALL serve stored file binaries to signed-in users. Anonymous access to files MUST NOT be permitted.

#### Scenario: Stored file is served

- GIVEN a stored document file and a signed-in user
- WHEN the user requests that file
- THEN the stored content is returned

#### Scenario: Anonymous request refused

- GIVEN a visitor with no signed-in session
- WHEN a file is requested
- THEN the request is refused

### Requirement: Normal-User Download

Normal users SHALL be able to download document files. File download authorization for non-administrators is a required capability.

#### Scenario: Normal user downloads a file

- GIVEN a signed-in normal user viewing an active document
- WHEN download is requested
- THEN the user receives the file binary

#### Scenario: Soft-deleted document file is not served

- GIVEN a document removed as obsolete (soft-deleted)
- WHEN a normal user requests its file
- THEN the download is refused

### Requirement: Storage at Confirmed Volume

File storage and retrieval SHALL operate at the confirmed volume: hundreds of documents, up to ~100 users.

#### Scenario: Files remain retrievable at volume

- GIVEN hundreds of stored document files
- WHEN signed-in users retrieve them
- THEN each stored file is returned intact

## Assumptions — Requires User Confirmation

- `ASSUMED — requires user confirmation`: accepted file formats and maximum upload size.
- `ASSUMED — requires user confirmation`: storage location and on-disk layout (design decision).
- `ASSUMED — requires user confirmation`: deployment target and operator (proposal-level).
