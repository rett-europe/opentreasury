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

export interface CandidateSheet {
  name: string;
  dataRowCount: number;
  headerRow: number;
}

export type IgnoredSheetReason = 'missing_required_headers' | 'empty' | string;

export interface IgnoredSheet {
  name: string;
  reason: IgnoredSheetReason;
  missing?: string[];
}

/**
 * Discovery payload returned by /imports/preview when the workbook has 2+
 * candidate movement sheets and no `sheet` query param was provided.
 *
 * Frontend should branch on `requiresSheetSelection` to decide whether to
 * render the sheet picker or the normal preview.
 */
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
  requiresSheetSelection: boolean;
  selectedSheet: string | null;
  availableSheets: string[];
  ignoredSheets: IgnoredSheet[];
  candidateSheets: CandidateSheet[];
}

export interface ExcelImportSummary {
  importBatchId: string;
  importMode: string;
  importSource: string;
  accountId: string;
  accountLabel: string;
  selectedSheet: string | null;
  categoriesCreated: number;
  subcategoriesAdded: number;
  transactionsImported: number;
  duplicatesSkipped: number;
  rowsSkipped: number;
  warnings: string[];
}
