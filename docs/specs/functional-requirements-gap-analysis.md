# Functional Requirements — Gap Analysis

**Date:** 2026-04-12  
**Analyst:** Niobe (Spec / UX Analyst)  
**Requested by:** Pedro (perocha)  
**Scope:** 34 functional requirements across 6 groups, compared against the current NGO Treasury implementation

---

## Summary Table

| FR | Title | Status | Gap Summary |
|----|-------|--------|-------------|
| **1. Financial source management** | | | |
| FR-001 | Manage financial sources | ✅ Implemented | Full CRUD for bank accounts + PayPal |
| FR-002 | Maintain financial source details | 🟡 Partial | Missing: generic provider field, explicit currency-per-account, unique identifier abstraction |
| FR-003 | Multiple active financial sources | ✅ Implemented | `isActive` toggle, no limit on active accounts |
| FR-004 | Assign transactions to a financial source | ✅ Implemented | `accountId` on every transaction, enforced during manual creation and import |
| **2. Transaction registration and ingestion** | | | |
| FR-005 | Import from external sources | 🟡 Partial | Excel import only (single "Full" mode). No PayPal/CSV/OFX. Bank mode (no categories sheet) not yet built |
| FR-006 | Manual transaction creation | ✅ Implemented | `POST /api/transactions` with full field set |
| FR-007 | Preserve original imported data | 🟡 Partial | `bankDescription` is stored, but no dedicated `originalData` or `importBatchId` field. No way to trace a transaction back to its import batch or raw row |
| FR-008 | Prevent duplicate transactions | ✅ Implemented | Composite key: `date + movementNumber + description + detail + |amount|` — checked at preview and import |
| FR-009 | Store key transaction attributes | 🟡 Partial | Missing: explicit `sourceReference` field (e.g., bank reference number distinct from `movementNumber`) |
| FR-010 | Track transaction direction and type | ⚠️ Conflicts | Direction is inferred from category type (income → positive, expense → negative). No explicit `transactionType` enum (income/expense/transfer/refund/adjustment). Category type drives amount sign — a transfer or refund doesn't fit cleanly into income/expense |
| FR-011 | Store counterparty information | ❌ Not implemented | No `payerName`, `payeeName`, or `counterpartyReference` fields in the transaction model |
| FR-012 | Support transaction corrections | 🟡 Partial | Transactions can be updated (`PUT`), but the original values are NOT preserved on the transaction itself — only in the audit log's `oldValues`/`newValues`. No `originalAmount`, `correctedAt`, or version history on the document |
| **3. Categorization and classification** | | | |
| FR-013 | Maintain category catalog | ✅ Implemented | Full CRUD, `isActive` toggle, referential integrity checks |
| FR-014 | Maintain subcategory catalog | ✅ Implemented | Nested in category document, add/update/deactivate supported |
| FR-015 | Assign category/subcategory per transaction | ✅ Implemented | `categoryId` + `subcategoryId` on every transaction |
| FR-016 | Support uncategorized transactions | ❌ Not implemented | `categoryId` and `subcategoryId` are **required** fields on `TransactionCreate`. The import also requires category+subcategory columns. No "uncategorized" sentinel or nullable category |
| FR-017 | Re-categorize transactions | ✅ Implemented | `PUT /api/transactions/{id}` allows changing `categoryId`/`subcategoryId`; amount is re-signed automatically |
| FR-018 | Validate classification consistency | 🟡 Partial | Amount auto-signing validates that category type matches sign direction. No explicit validation that subcategory belongs to the selected category |
| FR-019 | Categorization suggestions | ❌ Not implemented | No suggestion engine, no API endpoint, no ML/rule-based matching |
| FR-020 | Automatic categorization rules | ❌ Not implemented | No rule engine, no rule storage, no rule matching during import or creation |
| FR-021 | Track categorization status | ❌ Not implemented | No `categorizationStatus` field (uncategorized / auto-categorized / manually categorized / reviewed) on the transaction model |
| **4. Split transactions** | | | |
| FR-022 | Split a transaction into multiple lines | ❌ Not implemented | No split model, no API, no UI |
| FR-023 | Categorize split lines independently | ❌ Not implemented | (Depends on FR-022) |
| FR-024 | Validate split totals | ❌ Not implemented | (Depends on FR-022) |
| FR-025 | Edit or reverse splits | ❌ Not implemented | (Depends on FR-022) |
| **5. Transfers, refunds, and special movements** | | | |
| FR-026 | Identify internal transfers | ❌ Not implemented | No `isTransfer` flag, no transfer detection logic |
| FR-027 | Link transfer movements | ❌ Not implemented | No `linkedTransactionId` or transfer-pair linking |
| FR-028 | Support refunds and reversals | ❌ Not implemented | No `refundOf` field, no reversal workflow |
| FR-029 | Exclude neutral movements from reporting | ❌ Not implemented | Reports include all transactions; no filter for transfers/refunds |
| **6. Review and audit workflow** | | | |
| FR-030 | Review imported transactions | ❌ Not implemented | No `reviewStatus` field, no review queue, no review UI |
| FR-031 | Approve reviewed transactions | ❌ Not implemented | No approval workflow or status transitions |
| FR-032 | Flag transactions for follow-up | 🟡 Partial | Tags exist and could be used as flags (e.g., a "follow-up" tag), but there's no dedicated flagging model or workflow — it's improvised, not purpose-built |
| FR-033 | Add notes to transactions | 🟡 Partial | `detail` field exists and is editable, but it's a single text field, not a notes/comments thread. No timestamped notes from multiple users |
| FR-034 | Track reviewer identity | 🟡 Partial | `updatedBy`/`updatedByName` tracks who last changed a transaction. Audit log tracks all changes. But there's no explicit `reviewedBy`/`reviewedAt` field — the concept of "reviewer" doesn't exist in the model |

---

## Detailed Analysis by Group

### 1. Financial Source Management (FR-001 to FR-004)

**What exists today:**
- `AccountService` + `AccountCreate/Update/Response` schemas in [schemas.py](../../api/app/models/schemas.py)
- Fields: `bankName`, `bankNameShort`, `iban`, `paypalEmail`, `accountLabel`, `isPaypal`, `sortOrder`, `isActive`
- Full CRUD via [accounts.py](../../api/app/routers/accounts.py) router
- Referential integrity: cannot delete accounts with associated transactions (HTTP 409)
- Import auto-resolves accounts by IBAN or `bankNameShort` match

**Gaps:**
- **FR-002** — No generic `provider` field (e.g., "Unicaja", "BBVA", "PayPal"). Currently `bankName` serves this role but it's free-text, not structured. No `currency` per account — transactions carry currency individually, but the account itself doesn't declare its base currency. No `accountIdentifier` abstraction (IBAN for banks, email for PayPal — these are separate fields instead of a unified identifier model).
- **FR-004** — Fully covered. `accountId` is required on `TransactionCreate`.

**Verdict:** Solid foundation. Minor model enrichments needed for FR-002.

---

### 2. Transaction Registration and Ingestion (FR-005 to FR-012)

**What exists today:**
- `TransactionService` in [transaction_service.py](../../api/app/services/transaction_service.py): create, update, soft-delete, list, report queries, export queries
- `ImportService` in [import_service.py](../../api/app/services/import_service.py): Excel workbook import with preview/confirm flow
- Transaction fields: `date`, `valueDate`, `amount` (signed), `currency`, `balance`, `movementNumber`, `branchNumber`, `bankDescription`, `accountId`, `categoryId`, `subcategoryId`, `tagIds`, `detail`, `createdBy/At`, `updatedBy/At`, `isDeleted`
- Amount auto-signing based on `CategoryType` (income → positive, expense → negative)
- Duplicate detection via composite key

**Gaps:**

**FR-005 (Import from external sources):**
- Only one import mode exists: "Full" (requires categories sheet + category/subcategory columns in movements sheet)
- The planned "Bank" mode (import raw bank data without category info) is **not built** — this is the critical gap for the import improvements initiative
- No CSV, OFX, QIF, or PayPal format support
- No `importBatchId` to group transactions from the same import run

**FR-007 (Preserve original imported data):**
- `bankDescription` is preserved as-is from the import
- However, there is no `originalData` blob or `importSource` field
- No `importBatchId` — cannot trace a transaction back to a specific import run
- If the user edits `bankDescription`, the original is only recoverable from the audit log

**FR-009 (Key transaction attributes):**
- Most attributes covered: amount, currency, booking date (`date`), description (`bankDescription`), financial source (`accountId`)
- Missing: a dedicated `sourceReference` field for bank-specific references (currently `movementNumber` partially serves this, but some banks use a separate reference number)

**FR-010 (Transaction direction and type):** ⚠️ **Key conflict.**
- Current model: direction is **derived** from `CategoryType`. Income categories → positive amount. Expense categories → negative amount. There is no standalone `transactionType` field.
- The FR requests: explicit type enum (income, expense, transfer, refund, adjustment).
- **Problem:** Transfers between the organization's own accounts don't fit income/expense. A transfer from Bank A to Bank B would need to be coded as "expense" in A and "income" in B, which pollutes financial reports. Similarly, corrections/adjustments and refunds have no natural home.
- **This is the same conflict Pedro discussed with Neo (the category type discussion).** Resolution will require either:
  - (a) A `transactionType` field that coexists with `categoryType` (the type determines sign, but the category provides classification), or
  - (b) Special "system" categories for transfers/refunds/adjustments

**FR-011 (Counterparty information):**
- No fields exist for payer/payee name, reference text, or counterparty identification
- `bankDescription` often contains counterparty info but it's unstructured free text
- Fields needed: `counterpartyName`, `counterpartyReference` (or a simpler `payerPayee` field)

**FR-012 (Transaction corrections):**
- Editing is supported via `PUT /api/transactions/{id}`
- Original values ARE captured in the audit log (`oldValues`/`newValues` in the `AuditService`)
- However, the audit log is a separate collection with a 7-year TTL, not embedded in the transaction
- No `originalAmount`, `correctionReason`, `correctedAt` on the transaction itself
- No version numbering — the transaction document only has the latest state

**Verdict:** This group has the most critical gaps. FR-005 (Bank import mode), FR-010 (direction/type), and FR-016 (uncategorized) are blocking the import improvements initiative.

---

### 3. Categorization and Classification (FR-013 to FR-021)

**What exists today:**
- `CategoryService` in [category_service.py](../../api/app/services/category_service.py): full CRUD for categories and subcategories
- `CategoryType` enum: `income` | `expense` in [domain.py](../../api/app/models/domain.py)
- Categories embed subcategories as a nested array
- `isActive` toggle on both categories and subcategories
- Referential integrity checks before deletion

**Gaps:**

**FR-016 (Uncategorized transactions):** ❌ **Critical gap.**
- `TransactionCreate` schema requires `category_id: str` and `subcategory_id: str` — both are mandatory, non-optional strings
- The import service also requires `category` and `subcategory` columns in `REQUIRED_HEADERS`
- **For Bank import mode, this is a blocker.** Raw bank exports don't have categories. Transactions need to be importable without categories, then categorized later.
- Resolution options:
  - (a) Make `categoryId`/`subcategoryId` optional (nullable) in the schema and DB
  - (b) Create a system "Uncategorized" category and assign it by default
  - Approach (a) is cleaner but requires changes throughout (reports, exports, amount signing)

**FR-018 (Validate classification consistency):**
- Amount auto-signing validates category type ↔ sign direction
- But: **no validation that the subcategory belongs to the chosen category.** You could assign a subcategory from a different category and the API would accept it. This is a data integrity gap.

**FR-019 & FR-020 (Categorization suggestions & rules):** ❌
- No rule engine, no suggestion API, no ML integration, no pattern matching
- Pedro mentioned this as a future "rule engine" feature — not in current scope but included in the FRs for completeness

**FR-021 (Categorization status tracking):** ❌
- No `categorizationStatus` field on the transaction model
- The system cannot distinguish between: uncategorized, auto-categorized, manually categorized, or reviewed transactions
- This is essential for a review workflow (FR-030/031) and for bank import mode tracking

**Verdict:** FR-016 is the single biggest blocker. FR-018 (subcategory validation) is a data integrity gap. FR-019/020/021 are future work but the data model should be designed to accommodate them.

---

### 4. Split Transactions (FR-022 to FR-025)

**What exists today:** Nothing. There is no split concept in the data model, API, or UI.

**What would be needed:**
- A `splitLines` array (or child collection) on the transaction, each line having its own `categoryId`, `subcategoryId`, `amount`, and optional `detail`
- Validation: sum of split line amounts must equal the parent transaction amount
- API endpoints: `POST /api/transactions/{id}/split`, `PUT /api/transactions/{id}/split/{lineId}`, `DELETE /api/transactions/{id}/split` (unsplit / reverse)
- UI: split dialog, line-item editor, split indicator on transaction list
- Reporting: split-aware queries (aggregate by split-line categories, not parent category)

**Verdict:** Entirely new feature. No foundation exists. Should be prioritized after the core import improvements (Bank mode + uncategorized support).

---

### 5. Transfers, Refunds, and Special Movements (FR-026 to FR-029)

**What exists today:** Nothing. The system treats all transactions as independent income or expense entries.

**What would be needed:**
- **FR-026/027 (Transfers):** A `transactionType` field with at least `transfer` value. A `linkedTransactionId` field for pairing outbound/inbound legs. Detection heuristics (same amount, opposite sign, same day, different accounts).
- **FR-028 (Refunds):** A `refundOfTransactionId` field. Reversal logic that creates a counter-entry.
- **FR-029 (Reporting exclusions):** Report queries need a filter like `WHERE transactionType NOT IN ('transfer', 'refund', 'adjustment')`. Current reports in [reports.py](../../api/app/routers/reports.py) have no such filter.

**Verdict:** Entirely new. Dependent on resolving the FR-010 conflict (transaction type enum). This group is lower priority than Groups 2-3 but the data model should be designed with it in mind.

---

### 6. Review and Audit Workflow (FR-030 to FR-034)

**What exists today:**
- `AuditService` in [audit_service.py](../../api/app/services/audit_service.py): logs all entity changes with before/after values
- `AuditLogEntry` tracks: entity type, entity ID, action, `changedBy`/`changedByName`, timestamp, old/new values
- Audit API: `GET /api/audit` (admin-only) with pagination
- `updatedBy`/`updatedByName` on transactions

**Gaps:**

**FR-030 (Review imported transactions):** ❌
- No `reviewStatus` field on transactions
- No review queue concept (list of unreviewed transactions)
- No UI for reviewing imports

**FR-031 (Approve reviewed transactions):** ❌
- No approval status or workflow
- No status transitions (e.g., pending → reviewed → approved)

**FR-032 (Flag for follow-up):** 🟡
- Tags _could_ be repurposed for flagging, but:
  - Tags are general-purpose (color-coded labels), not purpose-built flags
  - No `isFlagged` boolean or `flagReason` field
  - No flag-filtered view or count

**FR-033 (Notes):** 🟡
- `detail` field exists but it's a single string, not a thread
- No `notes[]` array with author/timestamp per entry
- A proper notes system would need: `transactionNotes: [{id, text, author, authorName, createdAt}]`

**FR-034 (Reviewer identity):** 🟡
- `updatedBy`/`updatedByName` + audit log provide some tracking
- But no explicit `reviewedBy`/`reviewedAt`/`approvedBy`/`approvedAt` fields
- The concept of "reviewer" as a role action (distinct from "editor") doesn't exist

**Verdict:** The audit infrastructure is solid, but the review workflow is entirely missing. FR-030/031 are medium-priority — they become important once Bank import mode is live (because imported transactions need review before they're trusted).

---

## Data Model Gaps Summary

### Fields to ADD to Transaction document

| Field | Type | Purpose | Related FR |
|-------|------|---------|------------|
| `transactionType` | enum: `income`, `expense`, `transfer`, `refund`, `adjustment` | Explicit direction/type, decoupled from category | FR-010, FR-026, FR-028 |
| `categorizationStatus` | enum: `uncategorized`, `auto_categorized`, `manually_categorized`, `reviewed` | Track how/whether a transaction was categorized | FR-021, FR-016 |
| `counterpartyName` | string (optional) | Payer or payee name | FR-011 |
| `counterpartyReference` | string (optional) | Payer/payee reference text | FR-011 |
| `importBatchId` | string (optional) | Links transaction to its import run | FR-007 |
| `importSource` | string (optional) | Origin: `excel-full`, `excel-bank`, `manual`, `api` | FR-007 |
| `linkedTransactionId` | string (optional) | Pairs transfer legs; links refunds to original | FR-027, FR-028 |
| `reviewStatus` | enum: `pending`, `reviewed`, `approved`, `flagged` | Review workflow state | FR-030, FR-031, FR-032 |
| `reviewedBy` | string (optional) | Who reviewed | FR-034 |
| `reviewedAt` | datetime (optional) | When reviewed | FR-034 |
| `isFlagged` | boolean | Quick flag for follow-up | FR-032 |
| `flagReason` | string (optional) | Why flagged | FR-032 |
| `notes` | array of `{id, text, author, authorName, createdAt}` | Threaded notes | FR-033 |
| `splitLines` | array of `{id, categoryId, subcategoryId, amount, detail}` | Split transaction lines | FR-022, FR-023 |

### Fields to MODIFY on Transaction document

| Field | Current | Proposed Change | Related FR |
|-------|---------|-----------------|------------|
| `categoryId` | required `str` | Make optional (`str \| None`) | FR-016 |
| `subcategoryId` | required `str` | Make optional (`str \| None`) | FR-016 |

### New entities / enums needed

| Entity | Purpose | Related FR |
|--------|---------|------------|
| `TransactionType` enum | `income`, `expense`, `transfer`, `refund`, `adjustment` | FR-010 |
| `CategorizationStatus` enum | `uncategorized`, `auto_categorized`, `manually_categorized`, `reviewed` | FR-021 |
| `ReviewStatus` enum | `pending`, `reviewed`, `approved`, `flagged` | FR-030-032 |
| `ImportBatch` document | Tracks each import run (timestamp, file hash, user, row count, status) | FR-007 |
| `CategorizationRule` document | Stores auto-categorization rules (pattern → category mapping) | FR-020 |

---

## Priority Recommendations

### P0 — Must have for import improvements (Bank mode)

These are **blocking** the planned Bank Import mode and should be addressed first:

1. **FR-016: Make `categoryId`/`subcategoryId` optional** — Without this, bank imports cannot work (raw bank data has no categories). This requires changes in:
   - `TransactionCreate` schema (make fields optional)
   - `TransactionService.create_transaction()` (handle null category, skip auto-signing when uncategorized)  
   - `ImportService` (remove `category`/`subcategory` from `REQUIRED_HEADERS` for Bank mode)
   - Reports (handle uncategorized transactions gracefully)
   - Frontend transaction list (show "Uncategorized" badge)

2. **FR-010: Add `transactionType` field** — Even if only `income`/`expense` are supported initially, the field needs to exist so the model is extensible. Decide: does `transactionType` replace category-driven signing, or coexist with it?

3. **FR-021: Add `categorizationStatus` field** — Essential for tracking which imported transactions still need categorization. Default: `uncategorized` for bank imports, `manually_categorized` for manual creation.

4. **FR-005: Build Bank import mode** — The actual import logic for files without a categories sheet. Requires FR-016 to be resolved first.

### P1 — Important for near-term quality

5. **FR-007: Add `importBatchId` + `importSource`** — Traceability. Low effort, high value for debugging import issues.
6. **FR-011: Add counterparty fields** — Useful for bank import mode where bank descriptions often contain counterparty info.
7. **FR-018: Add subcategory-belongs-to-category validation** — Data integrity fix. Small change in `TransactionService`.

### P2 — Important but can follow

8. **FR-030/031/034: Review workflow** — Becomes critical once Bank imports are live (users need to review/approve imported transactions).
9. **FR-032/033: Flagging and notes** — Enhances the review workflow.
10. **FR-012: Transaction corrections with version preservation** — Currently only audit log captures changes. Consider adding `correctedAt` + `correctionReason` at minimum.

### P3 — Future work

11. **FR-019/020: Categorization suggestions and rules** — Rule engine. Pedro mentioned this. Design the `CategorizationRule` entity but don't build the engine yet.
12. **FR-022-025: Split transactions** — Entirely new feature. Complex. Should wait until the core model stabilizes.
13. **FR-026-029: Transfers, refunds, special movements** — Requires FR-010 (transaction type) to be resolved first. Design for it now, build later.

---

## Key Decision Points for the Team

1. **Transaction type vs. category type** — Should `transactionType` (income/expense/transfer/refund/adjustment) **replace** category-driven amount signing, or **coexist** with `categoryType`? This is architectural and affects reporting, import, and the entire sign-convention logic.

2. **Uncategorized strategy** — Make fields nullable (option A) or create a system "Uncategorized" category (option B)? Option A is more honest but requires null-safety everywhere. Option B is simpler but creates a fake category.

3. **Review workflow complexity** — Simple (pending → approved) or full (pending → reviewed → approved + flagged)? Depends on how many staff members will use the app and whether there's a separation between "person who imports" and "person who approves."

4. **Import batch tracking** — Lightweight (just an ID + timestamp) or full (file hash, row count, error log, revert capability)?

5. **Split transaction storage** — Embedded array on the parent transaction (simpler, Cosmos-friendly) or separate documents with a parent reference (more flexible, harder to query)?
