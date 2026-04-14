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
