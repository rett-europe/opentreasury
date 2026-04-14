# Cypher — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->

### 2026-04-14: Split transactions test suite written
- Created `api/tests/test_split_service.py` — 37 tests covering SplitService business logic:
  happy path (create/update/unsplit), validation (min 2 / max 20 lines, sum mismatch,
  already split, deleted, nonexistent, invalid category, orphan subcategory), amount sign
  handling (expense negative, income positive, transfer matches parent), and edge cases
  from spec §8 (category cleared, import batch preserved, decimal precision, unique IDs,
  sort order).
- Created `api/tests/test_router_split.py` — 17 tests covering the HTTP API layer:
  POST/PUT/DELETE `/api/transactions/{id}/split`, status codes (201/200/404/422/403),
  response shape verification (isSplit, splitCount, splitLines, splitCategoryIds).
- Pattern: service tests mock the repo (AsyncMock), router tests mock the service.
  Matches existing test_transaction_service.py and test_router_transactions.py patterns.
- Import expectations: `from app.services.split_service import SplitService`,
  `from app.services.dependencies import get_split_service`. These don't exist yet —
  Morpheus is implementing in parallel. Tests will fail at import until integration.
- Key file paths: `api/tests/test_split_service.py`, `api/tests/test_router_split.py`
- The make_transaction helper in conftest.py accepts arbitrary **overrides, so
  isSplit/splitCount/splitLines/splitCategoryIds can be passed directly.
- Black had persistent multiprocessing crashes on Pedro's Windows env (Python 3.11 +
  pathspec/typing_extensions conflict). Workaround: use `black.format_str()` as library.
  The venv's flake8 works fine.
- Pedro's decisions for split: min 2, max 20 lines; unsplit → categoryId=null,
  categorizationStatus="uncategorized"; one audit entry per operation.
