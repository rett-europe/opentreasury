# Electron + SQLite Desktop Mode Specification

**Author:** Neo (Lead/Architect)  
**Contributors:** Trinity (Frontend), Morpheus (Backend), Switch (Security), Tank (DevOps), Cypher (Testing), Niobe (UX), Oracle (Docs)  
**Requested by:** Issue #14  
**Date:** 2026-04-18  
**Status:** Draft — ready for technical validation

---

## 1. Problem

OpenTreasury currently runs as a web app (Angular + FastAPI + Cosmos DB + Entra ID).  
Issue #14 requests a desktop runtime with **Electron + SQLite**, feature parity with the current product, optional **OneDrive-based shared DB file**, and full alignment with the existing layered architecture.

## 2. Goal

Deliver a desktop deployment mode that:

1. Preserves all current functional capabilities (transactions, reports, import/export, audit, RBAC, preferences).
2. Reuses current Router → Service → Repository boundaries.
3. Uses SQLite as the persistence engine for desktop mode.
4. Supports collaborative operation through a OneDrive-synced SQLite file with explicit safety controls.
5. Keeps identity tracking consistent for audit purposes across local and shared modes.

## 3. Scope

### In Scope

- Electron shell around the Angular app.
- Desktop API runtime using existing FastAPI routers/services.
- New SQLite repository implementations behind current repository protocols.
- Configuration-driven repository provider selection (Cosmos vs SQLite).
- Desktop identity: OS username (local) or silent MSAL Microsoft account (OneDrive shared).
- No RBAC in desktop mode — all users are Admin. OneDrive folder permissions serve as coarse access control.
- Audit logging parity in SQLite.
- OneDrive shared-file collaboration mode with lock/conflict protections.

### Out of Scope

- Replacing existing cloud deployment.
- New business features.
- Multi-tenant desktop support.
- Real-time collaborative editing guarantees stronger than SQLite + OneDrive constraints can provide.

## 4. Architecture Alignment

### 4.1 Layering Rule (Must Keep)

Existing layering remains authoritative:

- **Routers:** unchanged contracts.
- **Services:** unchanged business rules.
- **Repositories:** add SQLite implementations; keep protocol interfaces stable.

Desktop mode introduces a storage adapter, not a domain rewrite.

### 4.2 Proposed Runtime Topology

1. Electron launches:
   - Angular UI (renderer process).
   - Local FastAPI process (localhost loopback only).
2. FastAPI uses existing services and dependency injection.
3. Repository provider resolves to SQLite implementations when `DATA_BACKEND=sqlite`.
4. SQLite file location is configured per environment (`local` or `onedrive-shared` path).

### 4.3 Data Mapping

Create SQLite-backed repositories for:

- `transactions`
- `categories`
- `reference_data`
- `audit_log`
- user preferences

Mapping must preserve current invariants:

- signed amount semantics
- soft-delete behavior
- referential integrity checks used by services
- audit immutability

## 5. Feature Parity Requirements

Desktop mode must match current behavior for:

- Authentication + Admin/Viewer authorization
- Dashboard
- Transactions CRUD + filters + pagination semantics
- Accounts/Categories/Tags management constraints
- Reports
- Export XLSX
- Import validation + confirm flow
- Reference data caching behavior
- Audit logging
- User preferences persistence

No feature may regress due to storage backend switch.

## 6. Authentication & Authorization

### 6.1 Desktop Auth Model (Different from Cloud)

Desktop mode does NOT replicate the cloud Entra ID app-registration model.
No tenant setup, no app roles, no OAuth consent screens.

| Mode | Identity source | How it works |
|------|----------------|-------------|
| **Local file** | OS username | App reads the current Windows/macOS username. No login prompt. |
| **OneDrive shared** | Microsoft account (via silent MSAL) | User is already signed into OneDrive. App reads identity silently — no popup, no separate login. |
| **Cloud (existing, unchanged)** | Entra ID with app roles | Full OAuth2 + RBAC. Not affected by this spec. |

### 6.2 RBAC — Not Implemented in Desktop Mode

- All desktop users are implicit Admin.
- Audit log still captures who did what (OS username or Microsoft account identity).
- NGOs wanting access control can use **OneDrive folder permissions** as a coarse RBAC layer:
  - Read+Write folder access → user can modify data.
  - Read-only folder access → SQLite blocks writes at OS level. No app code needed.
- Future enhancement (not in scope): in-app role table stored in SQLite.

### 6.3 Session Handling

- No tokens stored by the app in local mode.
- In OneDrive shared mode, MSAL acquires identity silently from the OS credential cache.
- No plaintext secrets in SQLite.

## 7. OneDrive Shared SQLite Mode

### 7.1 Support Model

OneDrive-shared SQLite is supported with strict constraints:

1. SQLite in WAL mode.
2. App-level advisory lock file (`.opentreasury.lock`) before writes.
3. Short write transactions only.
4. Automatic retry with backoff on lock contention.
5. Conflict detector using row version fields (`updated_at`, `version`) for optimistic concurrency in update paths.
6. Scheduled SQLite backup snapshots before schema migrations.

### 7.2 Identity in Shared Mode

- User identity resolved via silent MSAL (Microsoft account already signed into OneDrive).
- Audit entries stamped with Microsoft account name + email.
- No separate login flow — the app reads identity from the OS, not from a custom auth flow.

### 7.3 Operational Limits

- Supported for small teams with low simultaneous write volume.
- Not suitable for heavy concurrent editing.
- If lock/conflict thresholds are exceeded, teams must switch to cloud mode (Cosmos authoritative backend).

## 8. Security Requirements (Switch Gate)

1. Encrypt sensitive local secrets using OS secure store.
2. Optionally encrypt SQLite file at rest (SQLCipher or OS-level encrypted volume requirement).
3. Validate all imported files exactly as current backend flow does.
4. Keep audit trail tamper-evident (append-only service behavior + migration-safe schema constraints).
5. Disable external network exposure of desktop FastAPI (localhost only).

## 9. Implementation Phases

1. **Phase A — Foundations**
   - Add backend selector and SQLite repository skeletons.
   - Add migration framework for SQLite schema.
2. **Phase B — Functional parity**
   - Complete repository implementations and parity tests.
   - Wire Electron shell and local API startup.
3. **Phase C — Identity + security**
   - OS username identity for local mode, silent MSAL for OneDrive shared mode.
   - Localhost-only FastAPI hardening, SQLite file encryption decision.
4. **Phase D — OneDrive collaboration**
   - Advisory lock, conflict handling, stress tests, operational docs.
5. **Phase E — Packaging**
   - Signed installers (Windows/macOS), update strategy, rollback instructions.

## 10. Validation Criteria

Desktop mode is accepted only if:

1. Existing API/service unit tests pass against SQLite repositories (adapted test matrix).
2. Core end-to-end user journeys pass in Electron.
3. Security review confirms token/secret handling and localhost exposure controls.
4. OneDrive collaboration tests show no data corruption under expected NGO usage patterns.
5. Feature parity checklist is fully green.

## 11. Team Ownership

- **Neo:** architecture and repository boundary compliance.
- **Trinity:** Electron shell integration with Angular.
- **Morpheus:** SQLite repositories, migrations, backend DI wiring.
- **Switch:** auth/session/storage security hardening sign-off.
- **Tank:** packaging, installer pipeline, release automation.
- **Cypher:** parity, concurrency, and regression test strategy.
- **Niobe:** UX parity and desktop flow usability validation.
- **Oracle:** setup/runbook/update documentation.

## 12. Open Questions

1. Do we mandate SQLite file encryption or allow OS-disk encryption as minimum baseline?
2. What is the explicit supported user concurrency ceiling for OneDrive shared mode?
3. Should desktop mode support offline work when OneDrive sync is paused but the file is locally cached?
4. Is OneDrive shared mode GA or marked beta initially?
