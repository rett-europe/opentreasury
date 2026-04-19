// --- V2 enums ---
export type TransactionType = 'income' | 'expense' | 'transfer' | 'refund';
export type CategorizationStatus = 'uncategorized' | 'manually_categorized' | 'auto_categorized';
export type ReviewStatus = 'pending' | 'reviewed' | 'approved' | 'flagged';

// Named constants — use these instead of hardcoded strings
export const TRANSACTION_TYPES = {
  INCOME: 'income' as TransactionType,
  EXPENSE: 'expense' as TransactionType,
  TRANSFER: 'transfer' as TransactionType,
  REFUND: 'refund' as TransactionType,
} as const;

// --- Phase 3: Split transactions ---
export interface SplitLine {
  id: string;
  amount: number;
  categoryId: string | null;
  subcategoryId: string | null;
  tagIds: string[];
  detail: string | null;
  sortOrder: number;
}

export interface SplitLineCreate {
  amount: number;
  categoryId?: string | null;
  subcategoryId?: string | null;
  tagIds?: string[];
  detail?: string | null;
}

export interface SplitRequest {
  lines: SplitLineCreate[];
}

export interface TransactionNote {
  id: string;
  text: string;
  author: string;
  authorName: string | null;
  createdAt: string;
}

// Transaction — matches Cosmos DB transactions container
export interface Transaction {
  id: string;
  type: string;
  partitionKey: string; // "YYYY-MM"
  transactionType: TransactionType;
  date: string;
  valueDate: string;
  amount: number; // signed: negative = expense, positive = income
  currency: string;
  balance: number | null;
  movementNumber: string | null;
  branchNumber: string | null;
  bankDescription: string | null;
  accountId: string;
  categoryId: string | null;
  subcategoryId: string | null;
  categorizationStatus: string;
  reviewStatus: string;
  sourceReference: string | null;
  counterpartyName: string | null;
  counterpartyReference: string | null;
  tagIds: string[];
  detail: string | null;
  originalAmount: number | null;
  originalDate: string | null;
  notes: TransactionNote[];
  // --- Phase 3: Split ---
  isSplit: boolean;
  splitCount: number;
  splitLines: SplitLine[];
  splitCategoryIds: string[];
  // ---
  year: number;
  month: number;
  createdBy: string;
  createdByName: string;
  createdAt: string;
  updatedBy: string | null;
  updatedByName: string | null;
  updatedAt: string | null;
  reviewedBy: string | null;
  reviewedByName: string | null;
  reviewedAt: string | null;
  isDeleted: boolean;
}

export interface TransactionCreate {
  accountId: string;
  transactionType: TransactionType;
  date: string;
  valueDate?: string;
  amount: number; // signed
  bankDescription?: string;
  categoryId?: string | null;
  subcategoryId?: string | null;
  tagIds?: string[];
  detail?: string;
  movementNumber?: string;
  branchNumber?: string;
  currency?: string;
  balance?: number;
  sourceReference?: string;
  counterpartyName?: string;
  counterpartyReference?: string;
}

export interface TransactionUpdate {
  accountId?: string;
  transactionType?: TransactionType;
  date?: string;
  valueDate?: string;
  amount?: number;
  bankDescription?: string;
  categoryId?: string | null;
  subcategoryId?: string | null;
  tagIds?: string[];
  detail?: string;
  movementNumber?: string;
  branchNumber?: string;
  currency?: string;
  balance?: number;
  sourceReference?: string;
  counterpartyName?: string;
  counterpartyReference?: string;
  reviewStatus?: ReviewStatus;
}

export interface TransactionQueryParams {
  year: number;
  month: number;
  accountId?: string;
  categoryId?: string;
  subcategoryId?: string;
  tagId?: string;
  transactionType?: TransactionType;
  categorizationStatus?: CategorizationStatus;
  reviewStatus?: ReviewStatus;
  search?: string;
  amountMin?: number;
  amountMax?: number;
  includeDeleted?: boolean;
  pageSize?: number;
  continuationToken?: string;
}

// --- V2 request/response types ---
export interface ReviewStatusUpdate {
  reviewStatus: ReviewStatus;
}

export interface CategorizeRequest {
  categoryId: string | null;
  subcategoryId: string | null;
}

// --- Bulk categorize (see docs/specs/bulk-category-update-spec.md v1.1 §15 / A-1..A-4) ---

export interface BulkCategorizeItem {
  id: string;
  year: number;
  month: number;
}

export type BulkCategorizeAction = 'apply' | 'clear';

export interface BulkCategorizeRequest {
  items: BulkCategorizeItem[];
  action: BulkCategorizeAction;
  categoryId?: string | null;
  subcategoryId?: string | null;
}

/**
 * Stable per-row error codes returned by POST /api/transactions/bulk-categorize.
 * Keep this union in sync with `api/app/services/transaction_service.py::bulk_categorize`
 * and spec §15 / A-2. Unknown codes received from the server are tolerated and
 * rendered via the `message` field — the union is not used as a runtime type guard.
 */
export type BulkCategorizeFailureCode =
  | 'NOT_FOUND'
  | 'SPLIT_PARENT_NOT_BULK_UPDATABLE'
  | 'INVALID_SUBCATEGORY'
  | 'INACTIVE_CATEGORY'
  | 'CONCURRENCY_CONFLICT'
  | string;

export interface BulkCategorizeFailure {
  id: string;
  code: BulkCategorizeFailureCode;
  message: string;
}

export interface BulkCategorizeResponse {
  batchCorrelationId: string;
  succeeded: string[];
  failed: BulkCategorizeFailure[];
}

/** Frontend cap mirrors the server-side cap in spec §15 / A-3. */
export const BULK_CATEGORIZE_MAX = 200;

export interface NoteCreate {
  text: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  continuationToken: string | null;
  totalIncome: number;
  totalExpenses: number;
  net: number;
  transactionCount: number;
  uncategorizedCount: number;
}
