// Report response interfaces for GET /api/reports/*

export interface TransactionSummary {
  totalIncome: number;
  totalExpenses: number;
  net: number;
}

export interface CategorySummary {
  categoryId: string;
  categoryName: string;
  totalIncome: number;
  totalExpenses: number;
}

export interface BalanceItem {
  categoryId: string;
  categoryName: string;
  subcategoryId?: string;
  subcategoryName?: string;
  income: number;
  expense: number;
  net: number;
}

export interface MonthlySummary {
  year: number;
  month: number;
  totalIncome: number;
  totalExpenses: number;
  net: number;
}

export interface AccountSummary {
  accountId: string;
  totalIncome: number;
  totalExpense: number;
  net: number;
  transactionCount: number;
}
