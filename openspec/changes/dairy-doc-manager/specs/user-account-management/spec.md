# User Account Management Specification

## Purpose

Admin-provisioned accounts and authentication for the shared catalog: exactly two roles, no self-registration, no approval workflow. UI language requirement lives in `document-management` (Spanish, application-wide). Confirmed sources: enforcement checklist items 6, 9, 14, 15, plus auth confirmed in `sdd/dairy-doc-manager/proposal-answers`.

## Requirements

### Requirement: Two Roles

The system SHALL have exactly two roles: system administrator and normal user. Every account SHALL hold exactly one of these roles.

#### Scenario: Role assigned at provisioning

- GIVEN the administrator creating an account
- WHEN the account is saved
- THEN it carries exactly one role: system administrator or normal user

### Requirement: Administrator-Only Account Provisioning

The administrator SHALL create, edit, and deactivate user accounts. Self-registration and approval workflows MUST NOT exist anywhere in the system.

#### Scenario: Administrator creates an account

- GIVEN a signed-in administrator
- WHEN a new account is submitted
- THEN the account exists and its holder can sign in

#### Scenario: Administrator deactivates an account

- GIVEN an active account
- WHEN the administrator deactivates it
- THEN its holder can no longer sign in
- AND the account record remains in the system

#### Scenario: Administrator edits an account back to active

- GIVEN a deactivated account
- WHEN the administrator edits it to active
- THEN its holder can sign in again

#### Scenario: No self-registration path

- GIVEN an unauthenticated visitor
- WHEN the application is inspected for sign-up
- THEN no self-registration or approval request flow exists

### Requirement: Authentication Required

Access to the catalog and its files SHALL require a signed-in account. Anonymous access MUST NOT be provided.

#### Scenario: Unauthenticated access refused

- GIVEN a visitor with no signed-in session
- WHEN catalog access is attempted
- THEN access is refused until sign-in succeeds

### Requirement: Authorization Boundary for Account Management

Account management operations SHALL be restricted to the system administrator. Normal users MUST NOT create, edit, or deactivate accounts.

#### Scenario: Normal user attempts account management

- GIVEN a signed-in normal user
- WHEN an account create, edit, or deactivate action is issued
- THEN the action is refused
- AND no account data changes

### Requirement: Account Capacity

The system SHALL support up to approximately 100 user accounts (confirmed volume).

#### Scenario: Confirmed account volume works

- GIVEN ~100 provisioned accounts
- WHEN their holders sign in and use the catalog
- THEN sign-in and account administration work for every account

## Assumptions — Requires User Confirmation

- `ASSUMED — requires user confirmation`: whether more than one system administrator account may exist.
- `ASSUMED — requires user confirmation`: credential mechanics (password hashing, session/token lifetime) — design-phase detail; self-service password recovery is out of scope (checklist item 15).
- `ASSUMED — requires user confirmation`: deployment target and operator (proposal-level).
