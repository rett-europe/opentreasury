export interface AccountPreview {
  id: string;
  label: string;
  iban: string;
}

export interface NewCategoryPreview {
  name: string;
  suggestedType: string;
}

export interface NewSubcategoryPreview {
  categoryName: string;
  name: string;
}

export interface ImportPreview {
  valid: boolean;
  importMode: string;
  errors: string[];
  warnings: string[];
  totalRows: number;
  rowsWithErrors: number;
  account: AccountPreview;
  newCategories: NewCategoryPreview[];
  newSubcategories: NewSubcategoryPreview[];
  transactionsToImport: number;
  duplicatesToSkip: number;
}

export interface ExcelImportSummary {
  importBatchId: string;
  importMode: string;
  importSource: string;
  accountId: string;
  accountLabel: string;
  categoriesCreated: number;
  subcategoriesAdded: number;
  transactionsImported: number;
  duplicatesSkipped: number;
  rowsSkipped: number;
  warnings: string[];
}
