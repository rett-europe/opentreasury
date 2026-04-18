# Electron + SQLite Support Technical Specification

> **Author:** Neo (Lead) with Squad input  
> **Requested by:** Pedro (`perocha`)  
> **Status:** Draft — issue #14  
> **Date:** 2026-04-18  
> **Issue:** [#14](https://github.com/rett-europe/opentreasury/issues/14)

---

## 1. Problem

OpenTreasury is currently designed as a cloud web app:
- Angular SPA hosted in Azure Static Web Apps
- FastAPI backend in App Service
- Cosmos DB as the system of record
- Entra ID for authentication and RBAC

Issue #14 asks for a desktop-capable mode that:
1. Replicates current feature coverage
2. Uses SQLite for persistence
3. Allows multi-user sharing via OneDrive
4. Handles authentication
5. Preserves the existing layered architecture principles

---

## 2. Goals and Non-Goals

### Goals

- Deliver a desktop runtime using Electron without rewriting the product UI.
- Add SQLite persistence with feature parity for core CRUD, reports, import/export, and audit.
- Keep router → service → repository layering intact.
- Support authenticated users with role-aware behavior (Admin/Viewer).
- Support OneDrive-hosted shared database operation with explicit concurrency constraints.

### Non-Goals (Phase 1)

- Full offline-first merge engine with automatic conflict resolution.
- True concurrent multi-writer collaboration on the same SQLite file over OneDrive.
- Replacement of the existing cloud deployment model.

---

## 3. Architecture Strategy (Layered Integration)

### 3.1 Keep existing logical layers

The current layering remains unchanged:

`Router -> Service -> Repository Interface -> Repository Implementation`

### 3.2 Add repository implementation set for SQLite

Current Cosmos repositories remain. Add a parallel SQLite implementation:

- `api/app/repositories/sqlite/transaction_repo.py`
- `api/app/repositories/sqlite/category_repo.py`
- `api/app/repositories/sqlite/reference_item_repo.py`
- `api/app/repositories/sqlite/audit_repo.py`
- `api/app/repositories/sqlite/user_preferences_repo.py`

Repository selection is controlled by configuration (e.g., `DATA_BACKEND=cosmos|sqlite`).

### 3.3 Runtime variants

- **Cloud mode (existing):** Angular + FastAPI + Cosmos + Entra
- **Desktop mode (new):** Electron shell + local FastAPI + SQLite (+ optional cloud auth)

Electron hosts the Angular build and starts/monitors a bundled local API process.

---

## 4. SQLite Data Model Mapping

Create SQLite schema equivalents for current entities:

- `transactions`
- `categories`
- `reference_data`
- `audit_log`
- `user_preferences`

### Required parity rules

- Preserve signed amounts and `transactionType` semantics.
- Preserve soft delete behavior.
- Preserve audit logging on every write.
- Preserve report calculations and filters.
- Preserve import validation rules and duplicate detection.

### Schema and access rules

- Use migrations (`alembic` or equivalent migration mechanism).
- Enforce foreign keys where compatible with existing behavior.
- Add indexes for high-frequency filters (date range, account/category, review/categorization status).
- Enable WAL mode and busy timeout for resilience.

---

## 5. OneDrive Multi-User Model

### 5.1 Supported model

Use a **shared OneDrive folder** containing a single `opentreasury.db` file with explicit operating rules.

### 5.2 Concurrency policy (required)

- **Single active writer policy** for the shared file.
- App-level lock file (`opentreasury.db.lock`) with lease metadata.
- Read operations allowed broadly; write operations require active lease.
- Lease timeout + safe steal workflow for abandoned sessions.

### 5.3 Sync and failure handling

- Detect OneDrive conflict copies and block writes until resolved.
- Detect lock mismatch/staleness and surface actionable UI.
- Maintain append-only audit entries to support recovery review.
- Perform startup integrity checks (`PRAGMA integrity_check`) and backup rotation.

### 5.4 Practical limitation (must be explicit)

OneDrive + SQLite does **not** guarantee safe simultaneous multi-writer behavior.  
The supported mode is coordinated usage, not unrestricted concurrent editing.

---

## 6. Authentication and Authorization

### 6.1 Recommended approach

Keep Entra ID as the identity provider for desktop mode:

- Electron uses MSAL (public client flow) to sign users in.
- Access/id token claims are passed to local API requests.
- Local API validates token signature and issuer/audience when online.
- Role mapping continues to use existing `Admin` / `Viewer` claims.

### 6.2 Offline behavior

- Cache last successful identity and role claim set with expiry.
- Allow configurable offline grace window for previously authenticated users.
- Block privileged actions after expiry until re-authenticated online.

### 6.3 Alternative fallback (if Entra is unavailable for adopter)

- Local user store (hashed credentials) with role assignment.
- Explicitly marked as reduced-security fallback.
- Not default.

---

## 7. Packaging and Distribution

- Build Angular production bundle as desktop renderer assets.
- Bundle Python API and dependencies with Electron release.
- Configure app data directory for DB, logs, backups, and lock files.
- Provide signed installers for Windows first (NGO primary environment).

---

## 8. Rollout Plan

### Phase A — Foundations
- Add runtime configuration switch for repository backend.
- Implement SQLite connection manager and migration pipeline.
- Add repository implementations for all domain areas.

### Phase B — Desktop Runtime
- Create Electron host app.
- Launch embedded local API process.
- Wire renderer (Angular) to local API base URL.

### Phase C — Auth + RBAC
- Integrate Entra sign-in for desktop.
- Enforce role checks and offline claim policy.

### Phase D — OneDrive Shared Mode
- Implement lock lease protocol.
- Add conflict detection and operator UX.
- Add backup/restore and integrity utilities.

### Phase E — Hardening
- Parity test suite pass against SQLite backend.
- UAT with coordinated multi-user NGO workflow.
- Release documentation and operational runbook.

---

## 9. Acceptance Criteria

1. All existing functional areas operate in desktop mode with SQLite backend.
2. Router/service code paths require no architecture-breaking forks.
3. Admin/Viewer authorization works in desktop mode.
4. OneDrive shared DB mode prevents unsafe concurrent writes.
5. Audit log is complete for all write operations.
6. Import/export and reports match cloud-mode results for the same dataset.
7. Recovery guidance exists for lock contention and conflict-copy events.

---

## 10. Risks and Mitigations

- **Risk:** OneDrive conflict files during concurrent edits  
  **Mitigation:** strict writer lease, conflict detection, write block, operator workflow.

- **Risk:** Desktop packaging complexity (Python + Electron)  
  **Mitigation:** standardize build pipeline and artifact signing early.

- **Risk:** Feature drift between Cosmos and SQLite backends  
  **Mitigation:** backend-agnostic service tests + dual-backend CI matrix.

- **Risk:** Offline auth abuse  
  **Mitigation:** short offline grace TTL, privileged-action re-auth requirement.

---

## 11. Open Questions

1. Is strict single-writer policy acceptable for the NGO workflow, or is true concurrent collaboration mandatory?
2. What offline grace period is acceptable from a governance perspective?
3. Is local-auth fallback required for all adopters, or only exceptional tenants?
4. Should OneDrive shared mode be GA or opt-in beta behind a feature flag?

---

## 12. Definition of Done for Issue #14

Issue #14 is considered complete when:
- This specification is approved by maintainers.
- Architecture decisions (auth model + OneDrive concurrency model) are explicitly accepted.
- Follow-up implementation issues are created by phase with ownership.
