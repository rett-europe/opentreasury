# Balance Section - As-Built UX / Functional Spec

**Author:** Codex
**Requested by:** Manuel
**Date:** 2026-04-16
**Status:** Draft - reflects current implementation
**Scope:** Document the current `/balance` section exactly as implemented in frontend and backend
**Out of scope:** Redesign proposals, future enhancements, backend contract changes

---

## Overview

The `/balance` section presents an annual balance breakdown by category and subcategory. It uses a two-panel comparative layout:

- left panel for income
- right panel for expenses

Each panel has its own filters and sorting controls. The page also shows a top summary strip with:

- total income
- total expenses
- net balance

The page is yearly only. It does not support month-level filtering, date ranges, drill-down navigation, or exports.

---

## 1. Data Source

### Endpoint

`GET /api/reports/balance?year=YYYY`

### Frontend service

`frontend/src/app/core/services/report.service.ts`

### Backend implementation

- `api/app/routers/reports.py`
- `api/app/services/report_service.py`

### Response item shape

```ts
interface BalanceItem {
  categoryId: string;
  categoryName: string;
  subcategoryId?: string;
  subcategoryName?: string;
  income: number;
  expense: number;
  net: number;
}
```

### Backend aggregation rules

The backend behavior is:

- scope is annual only
- transactions are loaded with `get_transactions_for_report(year=year)`
- only transaction types `income` and `expense` are included
- `transfer` and `refund` are excluded
- split transactions are aggregated at split-line level
- non-split transactions are aggregated at transaction level
- grouping key is:
  - `categoryId:subcategoryId` when subcategory exists
  - `categoryId` when subcategory does not exist
- uncategorized rows use `categoryId = "uncategorized"`
- category and subcategory names are resolved from reference data
- each returned row already includes `income`, `expense`, and `net`

The backend does not return category subtotal rows.

---

## 2. Page Structure

The current page has this vertical structure:

```text
Hero
Summary strip
Loading state or two-table grid
```

### 2.1 Hero

The hero contains:

- section eyebrow using the balance label
- page title using the balance label
- subtitle using `balanceSubtitle`
- year selector on the right

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

### 2.2 Summary Strip

When the page is not loading, a three-card summary strip is shown with:

- total income
- total expenses
- net balance

These totals are computed from the processed annual dataset, not from visible filtered rows.

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

### 2.3 Main Content

When the page is not loading, the main content is a two-column grid:

- income panel
- expense panel

Each panel includes:

- panel title
- visible row count
- three local filters
- one local sortable table

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 3. Loading Behavior

When `loadBalance()` starts:

- `loading` is set to `true`
- the summary strip is hidden
- the tables are hidden
- a centered spinner is shown

When the request completes:

- `loading` is set to `false`
- data signals are updated
- visible rows are recalculated

If the request fails:

- the error is logged to console
- income rows become empty
- expense rows become empty
- totals become zero

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 4. Year Selection

The page supports selecting a year from a dropdown.

Rules:

- default selected year is `new Date().getFullYear()`
- available years are generated from current year minus 5 through current year
- changing the selected year immediately triggers `loadBalance()`

This is frontend-generated and not based on backend metadata.

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 5. Data Processing in Frontend

After the API response arrives, the frontend splits the dataset into two lists:

- `incomeRows`: rows where `income > 0`
- `expenseRows`: rows where `expense > 0`

Each list is initially sorted by:

1. `categoryName` ascending
2. `subcategoryName` ascending

Top-level totals are calculated as:

- `totalIncome = sum(incomeRows.income)`
- `totalExpense = sum(expenseRows.expense)`
- `netBalance = totalIncome - totalExpense`

Important note:

- the frontend does not use row-level `net` for rendering the tables
- the frontend only uses row-level `income` in the income table
- the frontend only uses row-level `expense` in the expense table

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 6. Income Panel

### Purpose

Display rows that have `income > 0`.

### Header

The panel header shows:

- title: total income label
- visible row count using `balanceVisibleRows(n)`

### Filters

The income panel has three local text filters:

- category
- subcategory
- amount

These filters only affect the income table.

### Table Columns

The income table has three columns:

- category
- subcategory
- amount

The amount column renders `item.income`.

### Empty state

If no visible income rows remain after filtering, the table shows:

- `balanceNoIncomeMatches`

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 7. Expense Panel

### Purpose

Display rows that have `expense > 0`.

### Header

The panel header shows:

- title: total expenses label
- visible row count using `balanceVisibleRows(n)`

### Filters

The expense panel has three local text filters:

- category
- subcategory
- amount

These filters only affect the expense table.

### Table Columns

The expense table has three columns:

- category
- subcategory
- amount

The amount column renders `item.expense`.

### Empty state

If no visible expense rows remain after filtering, the table shows:

- `balanceNoExpenseMatches`

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 8. Filtering Rules

Filtering is implemented separately for income and expense panels.

### 8.1 Category filter

- case-insensitive
- uses `includes()`
- trims user input

### 8.2 Subcategory filter

- case-insensitive
- uses `includes()`
- trims user input
- rows without subcategory are compared using `'-'`

### 8.3 Amount filter

The amount filter is a text match, not a numeric range.

Rules:

- trims user input
- replaces `,` with `.`
- converts the row amount to `value.toFixed(2)`
- uses string `includes()` matching

Examples:

- typing `500` matches `500.00`
- typing `50.0` may match any formatted amount containing that substring

This filter is applied to:

- `income` value in the income panel
- `expense` value in the expense panel

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 9. Sorting Rules

Sorting is implemented separately for income and expense panels.

### Sort fields currently supported

- `categoryName`
- `subcategoryName`
- `income`
- `expense`

### Default sort

Both panels default to:

- field: `categoryName`
- direction: `asc`

### Toggle behavior

When the user clicks a column header in a panel:

- if it is a different field, that field becomes active with ascending sort
- if it is the same field, direction toggles between ascending and descending

### Sort scope

- income sort only affects the income panel
- expense sort only affects the expense panel

### Group-preserving behavior

Rows are grouped by category before rendering.

If sorting by `categoryName`:

- categories are ordered by category name
- category cells are visually merged with `rowspan`

If sorting by any other field:

- groups are still ordered by category name
- rows are sorted inside each category group
- category cells are no longer merged
- each row shows its own category cell

This is an important current behavior detail: sorting by amount or subcategory does not produce one fully global ordering across the whole panel.

References:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 10. Grouping Rules

The frontend groups rows by category for display.

Rules:

- grouping key is `categoryId`, falling back to `categoryName`
- each group stores:
  - `categoryId`
  - `categoryName`
  - `rows`
- grouping is display-only
- no synthetic subtotal rows are created

The rendered grouping behavior depends on active sort:

- when sorted by category, the first row shows the category cell with `rowspan`
- following rows in the same group omit the category cell
- when sorted by another field, all rows show their own category cell

References:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 11. Responsive Behavior

### Desktop

- summary strip uses 3 columns
- main content uses 2 columns
- each table remains in its own panel

### Medium screens (`max-width: 1100px`)

- summary strip collapses to 1 column
- tables grid collapses to 1 column
- filter grids collapse to 1 column

### Small screens (`max-width: 720px`)

- page padding is reduced
- hero stacks vertically

Important current limitation:

- mobile keeps the same table-based two-panel structure
- there is no card-based mobile variant

Reference:

- `frontend/src/app/features/balance/balance.component.ts`

---

## 12. Labels Currently Used

The page currently depends on these labels:

- `balance`
- `balanceSubtitle`
- `year`
- `totalIncome`
- `totalExpenses`
- `netBalance`
- `balanceVisibleRows`
- `category`
- `subcategory`
- `amount`
- `balanceFilterCategoryPlaceholder`
- `balanceFilterSubcategoryPlaceholder`
- `balanceAmountPlaceholderIncome`
- `balanceAmountPlaceholderExpense`
- `balanceNoIncomeMatches`
- `balanceNoExpenseMatches`

Relevant files:

- `frontend/src/app/core/i18n/en.ts`
- `frontend/src/app/core/i18n/es.ts`
- `frontend/src/app/core/i18n/labels.type.ts`

---

## 13. Current Limitations

The current implementation has these functional and UX limitations:

- duplicated filter controls across the two panels
- duplicated sorting model across the two panels
- no row-level `net` column in the tables
- no unified comparison table
- no category subtotal rows
- no distinction between:
  - no data for selected year
  - no rows matching current filters
- no month or date-range filtering
- no export
- no mobile-specific structural variant

These are descriptive observations only. They are not proposed changes in this document.

---

## 14. Acceptance Criteria for Current Implementation

| ID | Acceptance Criteria |
|----|---------------------|
| AC-01 | The page loads data only from `GET /api/reports/balance?year=YYYY`. |
| AC-02 | The page displays a hero with title, subtitle, and year selector. |
| AC-03 | The page displays a summary strip with annual total income, annual total expenses, and annual net balance. |
| AC-04 | The page splits data into two panels: income rows and expense rows. |
| AC-05 | Each panel has its own local category, subcategory, and amount filters. |
| AC-06 | Each panel has its own independent sorting state. |
| AC-07 | The amount filter works as substring matching against formatted amounts, not as a numeric range. |
| AC-08 | Category grouping is visual only and uses rowspan when sorted by category. |
| AC-09 | Empty states are panel-specific: one for income matches and one for expense matches. |
| AC-10 | Responsive behavior stacks existing structures instead of replacing them with a different mobile pattern. |

---

## 15. Source References

- `frontend/src/app/features/balance/balance.component.ts`
- `frontend/src/app/core/services/report.service.ts`
- `frontend/src/app/shared/models/report.model.ts`
- `api/app/routers/reports.py`
- `api/app/services/report_service.py`
