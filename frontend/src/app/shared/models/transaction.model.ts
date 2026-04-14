// --- V2 enums ---
export type TransactionType = 'income' | 'expense' | 'transfer' | 'refund';
export type CategorizationStatus = 'uncategorized' | 'manually_categorized' | 'auto_categorized';
export type ReviewStatus = 'pending' | 'reviewed' | 'approved' | 'flagged';

export interface TransactionNote {
  id: string;
  text: string;
  author: string;
  authorName: string | null;
  createdAt: string;
}

export interface SplitLine {
  id: string;
  amount: number;
  categoryId: string | null;
  subcategoryId: string | null;
  tagIds: string[];
  detail: string | null;
}

export interface SplitLineCreate {
  amount: number;
  categoryId?: string | null;
  subcategoryId?: string | null;
  tagIds?: string[];
  detail?: string | null;
}

export interface SplitRequest {
  splits: SplitLineCreate[];
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
  splits: SplitLine[];
  isSplit: boolean;
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
