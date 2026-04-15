# Phase 3 — Split Transactions: Technical Research

**Version:** 1.0  
**Date:** 2026-04-14  
**Author:** Neo (Lead / Architect), with Morpheus-scope backend analysis  
**Requested by:** Pedro (perocha)  
**Status:** Approved — Pedro resolved open questions (2026-04-14)  
**Scope:** FR-022 to FR-025 implementation alternatives  
**Prerequisites:** Phase 1 (core model) must be complete. Phase 2 (import) should be complete.  
**Branch:** `feature/split-transactions`

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Data Model Alternatives](#2-data-model-alternatives)
3. [API Design Alternatives](#3-api-design-alternatives)
4. [Reporting Impact Analysis](#4-reporting-impact-analysis)
5. [Impact on Existing Code](#5-impact-on-existing-code)
6. [Recommendation](#6-recommendation)
7. [Resolved Questions](#7-resolved-questions)

---

## 1. Problem Statement

A user receives a single bank transaction (e.g., -€150.00 from Unicaja) but needs to allocate it across multiple budget categories: €100.00 for "Alquiler Local" and €50.00 for "Material Oficina." Today, the system is 1:1 — one transaction, one category. Split transactions break this into 1:N — one financial anchor, N categorized line items.

**Functional requirements (from gap analysis):**

| FR | Title | Summary |
|----|-------|---------|
| FR-022 | Split a transaction into multiple lines | Each line has its own amount, category, subcategory, tags, notes |
| FR-023 | Categorize split lines independently | Each line can have a different category/subcategory |
| FR-024 | Validate split totals | Sum of split line amounts must equal the parent transaction amount |
| FR-025 | Edit or reverse splits | Unsplit (remove all lines, revert to single transaction), edit individual lines |

**Key constraint:** The original transaction is the financial anchor. The bank statement says -€150.00 — that number is immutable. Split lines divide that amount for categorization purposes only; they do not create new financial movements.

---

## 2. Data Model Alternatives

### 2.1 Option A: Embedded Split Lines (Array in Transaction Document)

Split lines live as a nested array inside the parent transaction document.

```json
{
  "id": "tx-123",
  "type": "transaction",
  "partitionKey": "2026-03",
  "amount": -150.00,
  "transactionType": "expense",
  "isSplit": true,
  "splitCount": 2,
  "categoryId": null,
  "subcategoryId": null,
  "categorizationStatus": "manually_categorized",
  "splitLines": [
    {
      "id": "sl-uuid-1",
      "amount": -100.00,
      "categoryId": "cat-alquiler",
      "subcategoryId": "sub-local-sede",
      "tagIds": ["tag-mensual"],
      "detail": "Alquiler sede marzo",
      "sortOrder": 1
    },
    {
      "id": "sl-uuid-2",
      "amount": -50.00,
      "categoryId": "cat-material",
      "subcategoryId": "sub-oficina",
      "tagIds": [],
      "detail": "Material de oficina",
      "sortOrder": 2
    }
  ],
  "bankDescription": "PAGO PROVEEDOR MULTI",
  "accountId": "acc-unicaja001",
  "...": "...rest of transaction fields"
}
```

**When not split:** `isSplit = false`, `splitLines = []`, `categoryId`/`subcategoryId` are set normally on the parent — exactly like today.

#### Cosmos DB Query Patterns

**List transactions with splits:** `SELECT * FROM c WHERE c.partitionKey = @pk` — splits come back naturally because they're part of the document. Zero additional queries.

**Report queries (category aggregation):** Need to branch:
```sql
-- For split transactions, unroll the splitLines array
SELECT sl.categoryId, sl.amount
FROM c JOIN sl IN c.splitLines
WHERE c.partitionKey = @pk AND c.isSplit = true

-- UNION with non-split transactions
SELECT c.categoryId, c.amount
FROM c
WHERE c.partitionKey = @pk AND (c.isSplit = false OR NOT IS_DEFINED(c.isSplit))
```
Or do the branching in Python (simpler, current pattern already does Python-side aggregation).

**Filter by category across splits:** `SELECT * FROM c WHERE c.isSplit = true AND ARRAY_CONTAINS(c.splitLines, {"categoryId": @catId}, true)` — Cosmos supports partial matching in `ARRAY_CONTAINS`.

#### Analysis

| Criterion | Assessment |
|-----------|------------|
| **RU cost — reads** | ✅ Excellent. Single point-read (1 RU) returns the complete transaction + all split lines. No JOINs, no fan-out. |
| **RU cost — writes** | ✅ Good. Creating/updating splits is a single `replace_item` call. Atomicity is guaranteed — the entire document is written or not. |
| **RU cost — reports** | 🟡 Acceptable. Python-side aggregation already iterates all transactions. Adding a `for sl in tx.splitLines` loop is O(N×M) where M is avg split lines per tx — typically 2-5. Negligible overhead. |
| **Document size** | ✅ Safe. A split line is ~200–300 bytes. Even 50 split lines (absurd for an NGO) would add ~15KB. Transaction documents are currently ~1KB. Cosmos 2MB limit is not a concern. |
| **Consistency** | ✅ Atomic. All split lines are written in a single document replace. No partial-failure scenarios. |
| **Migration** | ✅ Trivial. Existing documents don't have `isSplit` or `splitLines`. Default-on-read: `isSplit = false`, `splitLines = []`. No backfill needed. |
| **Query complexity** | 🟡 Moderate. Cross-partition queries that filter by split-line category need `ARRAY_CONTAINS`. Not terrible, but less natural than a top-level `categoryId` filter. |
| **Code complexity** | ✅ Low. Single repository method for read/write. No multi-document coordination. |

#### Pros

1. **Atomic writes.** Split creation/update/unsplit is a single Cosmos `replace_item`. No transactional batch needed, no partial-failure recovery.
2. **Single read.** Listing transactions returns complete split info. No N+1 queries.
3. **Simple migration.** Zero-touch: old documents work as-is, new fields default on read.
4. **Partition-friendly.** Splits live in the same partition as their parent (same `partitionKey`). No cross-partition concerns.
5. **Matches existing patterns.** Categories already embed subcategories as a nested array. Notes are already embedded. The codebase has a precedent for this approach.

#### Cons

1. **Larger documents.** Each split line adds ~250 bytes. Normal case (2–5 lines) is negligible; edge cases (many splits) grow the document.
2. **No independent addressing.** Split lines don't have their own Cosmos document ID — they're identified by `splitLines[].id` within the parent. Can't do a point-read for a single split line.
3. **Concurrent edits.** If two users try to edit different split lines on the same transaction simultaneously, last-write-wins because the entire document is replaced. Mitigated by: (a) this is a small NGO with 1-2 admins, (b) the existing system already uses full-document replace.

---

### 2.2 Option B: Separate Documents (Split Lines as Child Documents)

Split lines are stored as independent documents in the same `transactions` container, linked to their parent via `parentTransactionId`.

```json
// Parent document
{
  "id": "tx-123",
  "type": "transaction",
  "partitionKey": "2026-03",
  "amount": -150.00,
  "isSplit": true,
  "splitCount": 2,
  "categoryId": null,
  "subcategoryId": null,
  "...": "...rest of fields"
}

// Child document 1
{
  "id": "sl-uuid-1",
  "type": "splitLine",
  "partitionKey": "2026-03",
  "parentTransactionId": "tx-123",
  "amount": -100.00,
  "categoryId": "cat-alquiler",
  "subcategoryId": "sub-local-sede",
  "tagIds": ["tag-mensual"],
  "detail": "Alquiler sede marzo",
  "sortOrder": 1,
  "createdBy": "oid-pedro-001",
  "createdAt": "2026-03-15T09:00:00Z"
}

// Child document 2
{
  "id": "sl-uuid-2",
  "type": "splitLine",
  "partitionKey": "2026-03",
  "parentTransactionId": "tx-123",
  "amount": -50.00,
  "categoryId": "cat-material",
  "subcategoryId": "sub-oficina",
  "tagIds": [],
  "detail": "Material de oficina",
  "sortOrder": 2,
  "createdBy": "oid-pedro-001",
  "createdAt": "2026-03-15T09:00:00Z"
}
```

#### Cosmos DB Query Patterns

**List transactions with splits:** Two queries required:
1. `SELECT * FROM c WHERE c.partitionKey = @pk AND c.type = 'transaction'` — gets transactions.
2. `SELECT * FROM c WHERE c.partitionKey = @pk AND c.type = 'splitLine'` — gets all split lines.
Then join in Python. Or a single query: `SELECT * FROM c WHERE c.partitionKey = @pk AND (c.type = 'transaction' OR c.type = 'splitLine')` and sort client-side.

**Report queries:** `SELECT c.categoryId, c.amount FROM c WHERE c.partitionKey = @pk AND c.type = 'splitLine'` UNION with non-split transactions query. Two queries, or one query with type discrimination.

**Get single transaction with splits:** Point-read for parent + query for children: `SELECT * FROM c WHERE c.parentTransactionId = @txId AND c.type = 'splitLine'`.

#### Analysis

| Criterion | Assessment |
|-----------|------------|
| **RU cost — reads** | ❌ Worse. Listing transactions requires fetching splits separately. Minimum 2 queries per page load, or a combined query that returns mixed document types. |
| **RU cost — writes** | 🟡 Mixed. Individual line CRUD is cheap (single point-write per line). But creating a split (parent update + N child creates) requires N+1 writes. No atomicity unless using Transactional Batch. |
| **RU cost — reports** | 🟡 Comparable. Can query `type = 'splitLine'` directly with a partition-scoped query. Similar RU to Option A's Python-side loop. |
| **Document size** | ✅ Excellent. Parent stays lean. Each split line is ~300 bytes in its own document. |
| **Consistency** | ❌ Risky. Creating 3 split lines requires 4 writes (parent + 3 children). If write 3 fails, you have an inconsistent state: parent says `splitCount: 3` but only 2 lines exist. Cosmos Transactional Batch mitigates this but adds complexity and is limited to same-partition operations. |
| **Migration** | ✅ Same as Option A. Existing docs unaffected. |
| **Query complexity** | 🟡 Higher. Every listing query must handle two document types. All existing queries need a `c.type = 'transaction'` filter to exclude split lines from transaction lists. **This is a breaking change to every existing query.** |
| **Code complexity** | ❌ High. Separate repository for split lines. Transaction list must merge parent + children. Unsplit must delete N children + update parent. Error recovery for partial writes. |

#### Pros

1. **Independent addressing.** Each split line has its own Cosmos document ID. Can point-read a single line.
2. **Smaller parent documents.** Parent doesn't grow with split lines.
3. **Natural for very large splits.** If a transaction had 100+ split lines (very unlikely for an NGO), individual documents scale better.

#### Cons

1. **Consistency gap.** Multi-document writes are not atomic without Transactional Batch. Partial failures create orphaned split lines or mismatched counts.
2. **Query contamination.** Split line documents in the transactions container pollute ALL existing queries. Every `SELECT * FROM c WHERE c.partitionKey = @pk` now returns mixed types. Every query needs `AND c.type = 'transaction'`.
3. **N+1 reads.** Getting a single transaction with its splits requires 1 point-read + 1 query (or Transactional Batch read, which has its own limits).
4. **Repository complexity.** Need a new `SplitLineRepository`, new protocols, new DI wiring. The transaction list endpoint must orchestrate merging.
5. **Cosmos serverless RU impact.** Each additional query costs minimum 2.5 RU. For a list page showing 50 transactions, adding a split-line query adds ~5-10 RU per page load.

---

### 2.3 Option C: Hybrid — Embedded Lines + Denormalized Category Summary

A variant of Option A where the parent document also carries a denormalized `splitCategorySummary` for fast filtering without reading the full `splitLines` array.

```json
{
  "id": "tx-123",
  "type": "transaction",
  "partitionKey": "2026-03",
  "amount": -150.00,
  "isSplit": true,
  "splitCount": 2,
  "splitCategoryIds": ["cat-alquiler", "cat-material"],
  "splitLines": [
    { "id": "sl-1", "amount": -100.00, "categoryId": "cat-alquiler", "...": "..." },
    { "id": "sl-2", "amount": -50.00, "categoryId": "cat-material", "...": "..." }
  ],
  "...": "..."
}
```

**`splitCategoryIds`** is a flat array of unique category IDs across all split lines, maintained automatically when splits are created/updated. This enables:
```sql
SELECT * FROM c WHERE ARRAY_CONTAINS(c.splitCategoryIds, @catId)
```

#### Analysis

| Criterion | Assessment |
|-----------|------------|
| **All of Option A's benefits** | ✅ Atomic, single-read, simple migration |
| **Category filter performance** | ✅ Better than Option A. `ARRAY_CONTAINS` on a flat string array is cheaper than partial-match on nested objects. |
| **Maintenance burden** | 🟡 Slight. `splitCategoryIds` must be kept in sync when split lines change. One extra line of code per write operation. |

#### Verdict on Option C

This is Option A with a minor optimization. The `splitCategoryIds` field is cheap to maintain and makes category-based filtering of split transactions faster. **If we go with embedded splits, this enhancement is worth including.**

---

### 2.4 Data Model Comparison Matrix

| Criterion | A: Embedded | B: Separate Docs | C: Hybrid |
|-----------|:-----------:|:-----------------:|:---------:|
| Read performance (list) | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| Write atomicity | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| RU efficiency | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Query simplicity | ⭐⭐ | ⭐ | ⭐⭐⭐ |
| Document size control | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Migration ease | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Code complexity | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| Consistency guarantees | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| **Total** | **21** | **12** | **22** |

---

## 3. API Design Alternatives

### 3.1 Option A: Atomic Split Operations (Batch)

All split lines are managed as a unit. You create, replace, or remove ALL lines at once.

```
POST   /api/transactions/{id}/split?year=YYYY&month=MM
  Body: { "lines": [ { "amount": -100, "categoryId": "...", ... }, ... ] }
  → Creates split lines. Parent becomes isSplit=true. Validates sum = parent amount.

PUT    /api/transactions/{id}/split?year=YYYY&month=MM
  Body: { "lines": [ { "amount": -100, "categoryId": "...", ... }, ... ] }
  → Fully replaces ALL split lines. All existing lines are discarded and new IDs are generated.
  → Input schema is identical to POST (SplitLineCreate has no id field).
  → Validates sum = parent amount after replacement.

DELETE /api/transactions/{id}/split?year=YYYY&month=MM
  → Removes all split lines (unsplit). Parent reverts to isSplit=false.
  → categoryId/subcategoryId on parent become null (uncategorized) — user must re-categorize.
```

#### Analysis

| Criterion | Assessment |
|-----------|------------|
| **Atomicity** | ✅ Excellent. The entire split state is set in one API call → one Cosmos write. Either all lines are saved or none. |
| **Validation** | ✅ Simple. Sum validation runs once against the complete set of lines. No intermediate invalid states. |
| **Undo/Unsplit** | ✅ Clean. `DELETE /split` removes everything in one call. |
| **Partial updates** | 🟡 Overhead. To change one line's category, the client sends ALL lines. But split lines are typically 2-5 items — the overhead is trivial. |
| **Frontend complexity** | ✅ Low. The UI builds the complete split state locally, sends it all at once. No need to track individual line IDs for CRUD. |
| **Idempotency** | ✅ `PUT` is naturally idempotent — same payload produces same result. |

#### Pros

1. **Single API call = single Cosmos write.** Maps perfectly to embedded data model (Option A/C).
2. **Validation is straightforward.** Check `sum(lines.amount) == parent.amount` once per request.
3. **No intermediate invalid states.** The transaction is either unsplit, or split with a valid set of lines.
4. **Simple error handling.** If validation fails, nothing changes.

#### Cons

1. **Full replacement on every edit.** To change one line, you send all lines. Acceptable for 2-5 lines; awkward if there were 50 (not our case).
2. **No granular audit trail.** The audit log shows "split lines replaced" rather than "line 2 category changed from A to B." Mitigated by diffing old vs. new lines in the audit entry.

---

### 3.2 Option B: Individual Line CRUD

Each split line is managed individually. Lines are added, updated, and removed one at a time.

```
POST   /api/transactions/{id}/split-lines?year=YYYY&month=MM
  Body: { "amount": -100, "categoryId": "...", ... }
  → Adds one split line. Parent becomes isSplit=true on first line.
  → WARNING: sum may not match parent until all lines are added.

PUT    /api/transactions/{id}/split-lines/{lineId}?year=YYYY&month=MM
  Body: { "amount": -80, "categoryId": "...", ... }
  → Updates one split line.

DELETE /api/transactions/{id}/split-lines/{lineId}?year=YYYY&month=MM
  → Removes one split line. If last line removed, auto-unsplit.

POST   /api/transactions/{id}/unsplit?year=YYYY&month=MM
  → Removes all split lines and reverts to non-split state.
```

#### Analysis

| Criterion | Assessment |
|-----------|------------|
| **Atomicity** | ❌ Poor. During multi-step split creation, the transaction is in an invalid state (sum doesn't match). Need a concept of "draft split" or deferred validation. |
| **Validation** | ❌ Complex. Either validate-on-every-write (blocks intermediate states) or defer validation (allows invalid states to persist). Both are messy. |
| **Undo/Unsplit** | 🟡 OK. `POST /unsplit` works, but also need to handle removing all lines one-by-one gracefully. |
| **Partial updates** | ✅ Natural. Change one line by ID. Clean semantics. |
| **Frontend complexity** | 🟡 Higher. Frontend must track line IDs, handle race conditions if auto-saving, manage the "sum doesn't match yet" intermediate state. |
| **Idempotency** | 🟡 POST is not idempotent. Retries create duplicates unless a client-generated ID is required. |

#### Pros

1. **Granular operations.** Can update one line without touching others. Good audit trail per-line.
2. **Standard REST semantics.** Follows typical nested resource patterns.
3. **Natural for large split counts.** If splits had 50+ lines, individual CRUD is more practical.

#### Cons

1. **Invalid intermediate states.** After adding line 1 of a 3-line split, the sum doesn't match. The system must either tolerate this (dangerous for reports) or introduce a "draft" concept (complexity).
2. **Multiple round-trips.** Creating a 3-line split requires 3 POST calls + 1 parent update. 4 API calls, 4 Cosmos writes.
3. **Validation headaches.** When does sum validation run? On every write? Only on a "finalize" endpoint? What if the user closes the browser after adding 2 of 3 lines?
4. **Concurrent modification risk.** Two requests hitting different split lines simultaneously could produce inconsistent Cosmos writes (full-document replace contention).

---

### 3.3 Option C: Hybrid — Batch with Optional Single-Line Update

Combines the strengths of both: batch operations for creation/unsplit, single-line update for quick edits.

```
POST   /api/transactions/{id}/split?year=YYYY&month=MM
  Body: { "lines": [ ... ] }
  → Creates all split lines at once. Validates sum.

PUT    /api/transactions/{id}/split?year=YYYY&month=MM
  Body: { "lines": [ ... ] }
  → Replaces ALL split lines. Validates sum.

PATCH  /api/transactions/{id}/split/{lineId}?year=YYYY&month=MM
  Body: { "categoryId": "new-cat", "detail": "updated note" }
  → Updates a single line's non-amount fields (category, subcategory, tags, detail).
  → Does NOT allow amount changes (those require full PUT to revalidate sum).

DELETE /api/transactions/{id}/split?year=YYYY&month=MM
  → Unsplit. Removes all lines.
```

This gives us batch atomicity for structural changes (amounts, adding/removing lines) and convenient single-line edits for categorization changes (the most common post-split operation).

---

### 3.4 API Design Comparison Matrix

| Criterion | A: Batch | B: Individual CRUD | C: Hybrid |
|-----------|:--------:|:------------------:|:---------:|
| Atomicity | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| Validation simplicity | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| Partial update convenience | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| Frontend simplicity | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| Cosmos write efficiency | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| Audit granularity | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Total** | **16** | **10** | **16** |

Options A and C score equally. C adds the convenience PATCH at the cost of one extra endpoint and a "no amount changes via PATCH" rule. Whether the extra endpoint is worth it depends on how often users re-categorize individual split lines after initial creation.

---

## 4. Reporting Impact Analysis

### 4.1 Current Report Query Pattern

The report service (`report_service.py`) already does Python-side aggregation. The Cosmos query in `query_for_report` fetches:

```sql
SELECT c.categoryId, c.accountId, c.amount, c.month, c.transactionType FROM c WHERE ...
```

Then Python loops iterate and bucket by category, account, or month. Key behavior:
- `transactionType == 'transfer'` or `'refund'` → excluded from income/expense totals
- `categoryId` is `None` → bucketed as `"uncategorized"`

### 4.2 Split-Aware Reporting Rules

**When a transaction IS split (`isSplit = true`):**
- The parent's `categoryId` is `null` (it has no single category — that's the point of splitting).
- Reports MUST aggregate at the split-line level, not the parent level.
- Each split line has its own `categoryId`, `amount`, and `transactionType` (inherited from parent).

**When a transaction is NOT split:**
- Behavior is identical to today. `categoryId` and `amount` from the parent document.

### 4.3 Query Changes per Data Model Option

#### Option A/C (Embedded) — Recommended

The `query_for_report` Cosmos query changes slightly to also fetch `isSplit` and `splitLines`:

```sql
SELECT c.categoryId, c.accountId, c.amount, c.month, c.transactionType,
       c.isSplit, c.splitLines
FROM c WHERE ...
```

Python aggregation changes:

```python
for item in items:
    txn_type = item.get("transactionType")
    if txn_type not in ("income", "expense"):
        continue

    if item.get("isSplit") and item.get("splitLines"):
        # Aggregate at split-line level
        for line in item["splitLines"]:
            cat = line.get("categoryId") or "uncategorized"
            amount = abs(Decimal(str(line["amount"])))
            buckets[cat][txn_type] += amount
    else:
        # Normal transaction — aggregate at parent level
        cat = item.get("categoryId") or "uncategorized"
        amount = abs(Decimal(str(item["amount"])))
        buckets[cat][txn_type] += amount
```

**RU impact:** The Cosmos query returns slightly larger documents (includes `splitLines` array). For a typical month with ~300 transactions and ~10% split, this adds maybe 2-5KB per query response. Negligible RU increase (existing query already returns the full projected fields; adding an array field doesn't change the query's index scan pattern).

#### Option B (Separate Documents)

Two queries needed:
```sql
-- Query 1: Non-split transactions
SELECT c.categoryId, c.amount, c.month, c.transactionType
FROM c WHERE c.partitionKey = @pk AND c.type = 'transaction'
  AND (c.isSplit = false OR NOT IS_DEFINED(c.isSplit))

-- Query 2: Split lines
SELECT c.categoryId, c.amount, c.month, c.parentTransactionId
FROM c WHERE c.partitionKey = @pk AND c.type = 'splitLine'
```

Then Python must: (a) handle the two result sets, (b) look up `transactionType` from the parent for each split line (either a third query or client-side join). More complex, more RU.

### 4.4 Non-Split Transactions — Zero Impact

Non-split transactions don't have `isSplit` or `splitLines`. The code check `if item.get("isSplit") and item.get("splitLines")` is `False` → falls through to the existing logic. **No behavioral change for non-split transactions.**

### 4.5 Summary Aggregates (Transaction List)

The `aggregate_filtered` method in `CosmosTransactionRepository` computes `total_income`, `total_expenses`, `net`, `transaction_count`, and `uncategorized_count`. For split-aware aggregation:

- **`total_income` / `total_expenses` / `net`:** These use the parent's `amount` and `transactionType`. Splits don't change these — the parent amount is the financial truth. **No change needed.**
- **`transaction_count`:** Counts parent transactions. Splits don't add to the count. **No change needed.**
- **`uncategorized_count`:** Currently counts transactions where `categoryId` is null. With splits: a split transaction has `categoryId = null` on the parent, but each line may be categorized. Option: don't count split transactions as "uncategorized" if all their lines have categories. This requires checking `splitLines` in the aggregate query. **Small change needed.**

---

## 5. Impact on Existing Code

### 5.1 Transaction Schemas ([schemas.py](../../api/app/models/schemas.py))

| Change | Scope | Notes |
|--------|-------|-------|
| New `SplitLineCreate` schema | New | `amount`, `categoryId`, `subcategoryId`, `tagIds`, `detail` |
| New `SplitLineResponse` schema | New | Adds `id`, `sortOrder` |
| New `SplitRequest` schema | New | `lines: list[SplitLineCreate]` |
| Add to `TransactionResponse` | Modification | `isSplit: bool = False`, `splitCount: int = 0`, `splitLines: list[SplitLineResponse] = []` |
| Add to `TransactionListResponse` | Possible | Whether to include `splitLines` in list view or only in detail view (performance vs. completeness). **Recommendation:** include `splitLines` — they're small and the frontend needs them for the split indicator + category pills. |

### 5.2 Domain Enums ([domain.py](../../api/app/models/domain.py))

No changes. Split transactions don't introduce new enum values.

### 5.3 Transaction Service ([transaction_service.py](../../api/app/services/transaction_service.py))

| Change | Scope | Notes |
|--------|-------|-------|
| `split_transaction()` | New method | Validates parent exists, not already split, sum matches. Sets `isSplit`, `splitLines` on document. |
| `update_split()` | New method | Replaces split lines. Re-validates sum. |
| `unsplit_transaction()` | New method | Clears `splitLines`, sets `isSplit = false`, `categoryId = null`. |
| `update_split_line()` | New method (if hybrid API) | Updates non-amount fields on a single split line. |
| `_validate_split_lines()` | New private method | Sum validation, per-line category validation, duplicate ID check. |
| `create_transaction()` | No change | New transactions are not split at creation time. |
| `update_transaction()` | Minor change | If transaction `isSplit`, prevent direct `categoryId` changes (category lives on split lines, not parent). |
| `categorize_transaction()` | Minor change | If `isSplit`, reject with "Cannot categorize a split transaction directly — update split lines instead." |

### 5.4 Transaction Repository ([transaction_repo.py](../../api/app/repositories/cosmos/transaction_repo.py))

| Change | Scope | Notes |
|--------|-------|-------|
| `query_for_report()` | Modification | Add `c.isSplit, c.splitLines` to SELECT projection |
| `aggregate_filtered()` | Modification | Handle uncategorized count for split transactions |
| All other methods | No change | Embedded data model means no new queries needed |

### 5.5 Transaction Router ([transactions.py](../../api/app/routers/transactions.py))

| Change | Scope | Notes |
|--------|-------|-------|
| `POST /api/transactions/{id}/split` | New endpoint | Admin only. Creates split. |
| `PUT /api/transactions/{id}/split` | New endpoint | Admin only. Replaces split lines. |
| `DELETE /api/transactions/{id}/split` | New endpoint | Admin only. Unsplit. |
| `PATCH /api/transactions/{id}/split/{lineId}` | New endpoint (if hybrid) | Admin only. Updates single line's non-amount fields. |

### 5.6 Report Service ([report_service.py](../../api/app/services/report_service.py))

| Method | Change | Notes |
|--------|--------|-------|
| `get_summary()` | No change | Uses parent `amount` and `transactionType` for totals. Splits don't change totals. |
| `get_by_category()` | Modification | Must unroll `splitLines` for category bucketing. |
| `get_monthly_trend()` | No change | Uses parent `amount` for monthly totals. |
| `get_by_account()` | No change | Uses parent `amount` and `accountId`. Splits don't move money between accounts. |

### 5.7 Export Service

The Excel export queries `query_for_export()` which returns full transaction documents. For split transactions:

| Approach | Effort |
|----------|--------|
| **Option 1:** Export parent row + child rows (one row per split line, indented or marked) | Medium. Requires reformatting the export logic to unroll splits. |
| **Option 2:** Export parent row only, with a "Split: 2 lines" column | Low. Add a column, ignore split lines in export. |
| **Recommendation:** Option 1 — the export is for accounting, and accountants need category-level detail. |

### 5.8 Import Service

Can an imported transaction be split immediately during import? **No.** Import creates raw transactions (often uncategorized in Bank mode). Splitting is a post-import categorization action. The import service needs **no changes**.

### 5.9 Audit Trail

Split operations should be audited like any other transaction mutation:

| Operation | Audit Entry |
|-----------|-------------|
| Create split | `action: "Update"`, `newValues: { isSplit: true, splitLines: [...] }` |
| Update split | `action: "Update"`, `oldValues: { splitLines: [...old] }`, `newValues: { splitLines: [...new] }` |
| Unsplit | `action: "Update"`, `oldValues: { isSplit: true, splitLines: [...] }`, `newValues: { isSplit: false, splitLines: [] }` |

The existing audit infrastructure handles this — `AuditService.log()` accepts arbitrary `old_values`/`new_values` dicts.

### 5.10 Repository Protocol ([protocols.py](../../api/app/repositories/protocols.py))

No new protocol methods needed if we use the embedded model (Option A/C). The existing `replace()` method handles split writes. The existing `query_for_report()` just needs its projected fields updated in the Cosmos implementation.

---

## 6. Recommendation

### Data Model: Option C (Embedded + Category Summary)

**Go with embedded split lines in the transaction document, plus a `splitCategoryIds` convenience array.**

**Rationale:**

1. **Atomicity is non-negotiable for financial data.** An NGO tracking real money cannot have "split line 2 of 3 saved but line 3 failed." Embedded = single Cosmos write = atomic. Option B's multi-document writes introduce failure modes that require complex recovery logic for a team of 1-2 developers.

2. **Matches existing patterns.** Categories already embed subcategories. Notes are already embedded in transactions. The codebase is designed around rich, self-contained documents. Option B would be the first entity-relationship pattern in a document-oriented system — it fights the grain.

3. **RU cost wins.** Serverless Cosmos charges per RU. Embedded reads are 1 RU point-reads. Option B's fan-out queries cost 3-5x more per page load. At NGO scale (~300 tx/month), the absolute cost difference is small, but there's no reason to pay more for a worse developer experience.

4. **Document size is a non-issue.** A typical split is 2-5 lines × ~250 bytes = 0.5-1.25KB added. The 2MB Cosmos limit is ~1600x larger. Even pathological cases (50 lines) are well within limits.

5. **Migration is zero-effort.** Old documents work without modification. `isSplit` defaults to `false` on read. No backfill scripts, no downtime.

6. **The `splitCategoryIds` optimization costs almost nothing** (one array update per split write) and enables efficient category-based filtering of split transactions without nested `ARRAY_CONTAINS`.

### API Design: Option A (Batch Operations)

**Go with atomic batch split operations: POST to create, PUT to replace all lines, DELETE to unsplit.**

**Rationale:**

1. **Maps 1:1 to the data model.** Batch API → single document write → atomic Cosmos operation. The simplest possible stack.

2. **Validation is trivial.** `sum(lines.amount) == parent.amount` runs once per request against the complete set. No intermediate invalid states, no "draft split" concept.

3. **Frontend is happier.** The split dialog collects all lines, sends them all at once. No line-ID tracking, no race conditions, no "what if I close the browser mid-split."

4. **The hybrid PATCH (Option C API) can be added later.** If Niobe's UX analysis shows that users frequently re-categorize individual split lines after creation, we add a `PATCH /split/{lineId}` endpoint for non-amount changes. It's additive — no breaking changes.

5. **2-5 lines per split.** Individual line CRUD (Option B) solves a problem we don't have. It's designed for large collections of sub-resources, not 2-5 categorization entries.

### Combined: Embedded + Batch = Maximum Simplicity

| Decision | Choice |
|----------|--------|
| Data model | Embedded split lines + `splitCategoryIds` array |
| API | Batch operations (POST/PUT/DELETE /split) |
| Reports | Python-side split-line unrolling in `get_by_category()` |
| Export | Unroll split lines into separate rows |
| Import | No changes (splitting is post-import) |
| Audit | Existing audit service, diff old/new split lines |
| Migration | Zero-touch (defaults on read) |

---

## 7. Resolved Questions

All questions resolved by Pedro (2026-04-14).

### Pedro's Decisions

1. **Split line limit:** Minimum 2, maximum 20. Confirmed.
2. **Unsplit behavior:** Parent category reverts to uncategorized (null). Confirmed.
3. **Split in transaction list view:** Show split indicator on the transaction row, details expand/collapse on click. Split lines are NOT separate rows. Fetch full split data inline for the detail view.
4. **Can transfers/refunds be split?** Allowed — some NGOs split a transfer's purpose across budget lines.
5. **Parent category after split:** Set to indicate "Split" status — the parent category no longer applies.
6. **Re-split:** Allowed — existing split can be edited via PUT endpoint.
7. **Audit:** Log the entire split operation as ONE audit entry when saved.
8. **Import + split:** Split only AFTER import, never during.
9. **Export:** Respect hierarchy but defer export changes to a follow-up phase.

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Split lines bloat transaction documents beyond comfortable sizes | Very Low | Low | Cap at 20 lines. Typical usage is 2-5. |
| Concurrent split edits from two admins cause last-write-wins data loss | Low | Medium | Same risk exists today for transaction edits. NGOs have 1-2 admins. Future: ETags for optimistic concurrency. |
| Report performance degrades with many split transactions | Low | Low | Python-side loop is O(N×M). With ~300 tx/month and avg 3 split lines, this is ~1000 iterations. Sub-millisecond. |
| Export becomes confusing with multi-row splits | Medium | Medium | Clear visual formatting in Excel: parent row + indented child rows. Header: "Split lines of TX-123." |
| Users create a split then never match the sum (save with wrong amounts) | Zero | — | API validates `sum == parent.amount` on every write. Cannot save an invalid split. |

---

## Appendix A: Split Line Schema (Proposed)

```python
class SplitLineCreate(CamelModel):
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    tag_ids: list[str] = []
    detail: Optional[str] = Field(default=None, max_length=500)


class SplitLineResponse(CamelModel):
    id: str
    amount: Decimal
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    tag_ids: list[str] = []
    detail: Optional[str] = None
    sort_order: int = 0


class SplitRequest(CamelModel):
    lines: list[SplitLineCreate] = Field(min_length=2, max_length=20)
```

## Appendix B: Cosmos Document After Split (Complete Example)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "type": "transaction",
  "partitionKey": "2026-03",
  "date": "2026-03-15",
  "valueDate": "2026-03-15",
  "year": 2026,
  "month": 3,
  "amount": -150.00,
  "currency": "EUR",
  "balance": 12345.67,
  "movementNumber": "00234",
  "branchNumber": "0049",
  "sourceReference": "TRF-2026-00234",
  "bankDescription": "PAGO PROVEEDOR MULTI",
  "accountId": "acc-unicaja001",
  "transactionType": "expense",
  "categoryId": null,
  "subcategoryId": null,
  "categorizationStatus": "manually_categorized",
  "isSplit": true,
  "splitCount": 2,
  "splitCategoryIds": ["cat-alquiler-001", "cat-material-002"],
  "splitLines": [
    {
      "id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
      "amount": -100.00,
      "categoryId": "cat-alquiler-001",
      "subcategoryId": "sub-local-sede",
      "tagIds": ["tag-mensual"],
      "detail": "Alquiler sede marzo 2026",
      "sortOrder": 1
    },
    {
      "id": "a9b8c7d6-e5f4-3210-fedc-ba0987654321",
      "amount": -50.00,
      "categoryId": "cat-material-002",
      "subcategoryId": "sub-oficina",
      "tagIds": [],
      "detail": "Material de oficina",
      "sortOrder": 2
    }
  ],
  "counterpartyName": "Proveedor Multiservicio S.L.",
  "counterpartyReference": null,
  "reviewStatus": "approved",
  "reviewedBy": "oid-maria-001",
  "reviewedByName": "María García",
  "reviewedAt": "2026-03-16T10:30:00Z",
  "originalAmount": null,
  "originalDate": null,
  "tagIds": [],
  "detail": null,
  "notes": [],
  "importBatchId": null,
  "importSource": null,
  "createdBy": "oid-pedro-001",
  "createdByName": "Demo Admin",
  "createdAt": "2026-03-15T09:00:00Z",
  "updatedBy": "oid-maria-001",
  "updatedByName": "María García",
  "updatedAt": "2026-03-16T10:25:00Z",
  "isDeleted": false
}
```

## Appendix C: API Endpoint Summary (Proposed)

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `POST` | `/api/transactions/{id}/split?year=YYYY&month=MM` | `SplitRequest` | Create split lines (transaction must not already be split) |
| `PUT` | `/api/transactions/{id}/split?year=YYYY&month=MM` | `SplitRequest` | Replace all split lines (transaction must be split) |
| `DELETE` | `/api/transactions/{id}/split?year=YYYY&month=MM` | — | Unsplit (remove all lines, revert to non-split) |
| `GET` | `/api/transactions/{id}?year=YYYY&month=MM` | — | Returns full transaction including `splitLines` (existing endpoint, no change) |

All endpoints require Admin role. Split data is included in existing list/detail responses — no separate "get split lines" endpoint needed.
