export interface AppLabels {
  // Navigation
  newTransaction: string;
  dashboard: string;
  transactions: string;
  balance: string;
  balanceSubtitle: string;
  netBalance: string;
  balanceVisibleRows: (n: number) => string;
  balanceFilterCategoryPlaceholder: string;
  balanceFilterSubcategoryPlaceholder: string;
  balanceAmountPlaceholderIncome: string;
  balanceAmountPlaceholderExpense: string;
  balanceNoIncomeMatches: string;
  balanceNoExpenseMatches: string;
  categories: string;
  tags: string;
  accounts: string;
  export: string;
  import: string;
  // Settings
  settingsTitle: string;
  settingsSubtitle: string;
  language: string;
  spanish: string;
  english: string;
  appearance: string;
  light: string;
  dark: string;
  compactMode: string;
  compactModeHint: string;
  reducedMotion: string;
  reducedMotionHint: string;
  moreSoon: string;
  logout: string;
  menu: string;
  openSettings: string;
  // Common field/column labels
  date: string;
  account: string;
  notes: string;
  category: string;
  subcategory: string;
  amount: string;
  tag: string;
  detail: string;
  name: string;
  description: string;
  order: string;
  color: string;
  type: string;
  // Common actions
  cancel: string;
  save: string;
  saving: string;
  update: string;
  close: string;
  // Filters
  year: string;
  month: string;
  allMonths: string;
  allItems: string;
  search: string;
  searchPlaceholder: string;
  minAmount: string;
  maxAmount: string;
  // Month names
  monthNames: readonly [
    string, string, string, string,
    string, string, string, string,
    string, string, string, string,
  ];
  // Dashboard
  accountBalances: string;
  transactionCountSuffix: string;
  monthlySummary: string;
  totalIncome: string;
  totalExpenses: string;
  totalNet: string;
  recentTransactions: string;
  noTransactionsThisMonth: string;
  // Transactions
  editTransaction: string;
  valueDate: string;
  incomeIndicator: string;
  expenseIndicator: string;
  amountEur: string;
  saveAndNew: string;
  transactionSaved: string;
  deleteTransactionConfirm: string;
  // Categories
  newCategory: string;
  editCategory: string;
  incomeType: string;
  expenseType: string;
  subcategories: string;
  subcategoryName: string;
  noSubcategories: string;
  noCategoriesEmpty: string;
  categorySaveError: string;
  deleteCategoryConfirm: (name: string) => string;
  addSubcategory: string;
  noSubcategoriesYet: string;
  activeCategory: string;
  // Tags
  newTag: string;
  editTag: string;
  noTagsEmpty: string;
  tagSaveError: string;
  deleteTagConfirm: (tagName: string) => string;
  presetColors: string;
  otherColor: string;
  tagPreview: string;
  inactiveLabel: string;
  // Accounts
  bankAccounts: string;
  newAccount: string;
  editAccount: string;
  bankName: string;
  shortName: string;
  accountLabel: string;
  paypalAccount: string;
  paypalEmail: string;
  noAccountsEmpty: string;
  accountSaveError: string;
  accountDeleteError: string;
  bankType: string;
  paypalType: string;
  ibanLabel: string;
  colorLabel: string;
  activateAccount: (label: string) => string;
  deactivateAccount: (label: string, count: number) => string;
  deactivateAccountNoTx: (label: string) => string;
  accountActivated: (label: string) => string;
  accountDeactivated: (label: string) => string;
  deleteAccountConfirm: (label: string) => string;
  // Export
  exportToExcel: string;
  exportSubtitle: string;
  dateFrom: string;
  dateTo: string;
  downloading: string;
  downloadExcel: string;
  // Import
  importBankTemplate: string;
  importSubtitle: string;
  selectXlsx: string;
  unicajaDescription: string;
  chooseExcel: string;
  validating: string;
  previewBtn: string;
  whatImportDoes: string;
  importStep1: string;
  importStep2: string;
  importStep3: string;
  importStep4: string;
  validationFailed: string;
  fixErrorsBeforeImport: string;
  previewTitle: string;
  newAccountSuffix: string;
  newCategoriesCount: string;
  newSubcategoriesCount: string;
  transactionsToImport: string;
  duplicatesToSkip: string;
  totalRows: string;
  categoriesToCreate: string;
  subcategoriesToCreate: string;
  importWarnings: string;
  confirmImportBtn: string;
  importing: string;
  importResultTitle: string;
  importModeFull: string;
  importModeInline: string;
  importModeBank: string;
  bankModeNotice: string;
  bankModeSummaryNotice: string;
  inferred: string;
  importStatementBtn: string;
  importBatchId: string;
  inlineModeNotice: string;
  importSelectAccount: string;
  importSelectAccountPlaceholder: string;
  importStepAccount: string;
  importStepFile: string;
  importNewCategories: string;
  importCategoryTypeIncome: string;
  importCategoryTypeExpense: string;
  importCategoryTypeHint: string;
  categoriesCreated: string;
  subcategoriesAdded: string;
  transactionsImported: string;
  duplicatesSkipped: string;
  rowsSkipped: string;
  totalCategoriesLoaded: string;
  importValidateError: string;
  importError: string;
  importedCount: (n: number) => string;
  // Multi-sheet selection (issue #17)
  importSheetSelectorTitle: string;
  importSheetSelectorHelp: string;
  importSheetSelectorRows: (n: number) => string;
  importSheetSelectorIgnored: (n: number) => string;
  importSheetBadge: (name: string) => string;
  importSheetReasonNoHeaders: (list: string) => string;
  importSheetReasonEmpty: string;
  importSheetSelectionRequired: string;
  importPickSheetFirst: string;
  importDuplicateDetails: (n: number) => string;
  importDuplicateRow: string;
  importIncludeDuplicates: string;
  // --- Phase 1: Transaction Type ---
  transactionType: string;
  incomeOption: string;
  expenseOption: string;
  transferInOption: string;
  transferOutOption: string;
  refundReceivedOption: string;
  refundGivenOption: string;
  transferType: string;
  refundType: string;
  // --- Phase 1: Type indicators ---
  incomeIndicatorV2: string;
  expenseIndicatorV2: string;
  transferInIndicator: string;
  transferOutIndicator: string;
  refundReceivedIndicator: string;
  refundGivenIndicator: string;
  // --- Phase 1: Category optional ---
  categoryOptional: string;
  subcategoryOptional: string;
  uncategorizedLabel: string;
  clearCategory: string;
  // --- Phase 1: Additional details ---
  additionalDetails: string;
  counterpartyName: string;
  counterpartyReference: string;
  sourceReference: string;
  // --- Phase 1: Notes ---
  notesSection: string;
  noteCount: (n: number) => string;
  addNote: string;
  addNotePlaceholder: string;
  noteAdded: string;
  // --- Phase 1: Review status ---
  reviewStatus: string;
  statusPending: string;
  statusReviewed: string;
  statusApproved: string;
  statusFlagged: string;
  changeStatus: string;
  lastReviewedBy: string;
  reviewStatusUpdated: string;
  // --- Phase 1: Filters ---
  categorizationFilter: string;
  uncategorizedOnly: string;
  manuallyCategorized: string;
  reviewStatusFilter: string;
  // --- Phase 1: List summary ---
  transactionCount: (n: number) => string;
  uncategorizedCount: (n: number) => string;
  transfersTotal: string;
  // --- Phase 1: Account ---
  currency: string;
  // --- Phase 1: Quick categorize ---
  quickCategorize: string;
  categorizeTitle: string;
  categorizeButton: string;
  categorizationSaved: string;
  // --- Navigation sections ---
  sectionMain: string;
  sectionConfig: string;
  sectionData: string;
  // --- Confirm dialog defaults ---
  confirmDefault: string;
  cancelDefault: string;
  // --- Phase 3: Split transactions ---
  splitTransaction: string;
  editSplit: string;
  splitDialogTitle: string;
  splitLines: string;
  addLine: string;
  removeSplit: string;
  saveSplit: string;
  splitAllocated: string;
  splitUnallocated: string;
  splitOverAllocated: (amount: string) => string;
  splitBalanced: string;
  splitMinLinesError: string;
  splitRemoveConfirm: (count: number) => string;
  splitSaved: string;
  splitRemoved: string;
  splitIndicator: (count: number) => string;
  splitDiscardConfirm: string;
  splitLineAmountRequired: string;
  // --- Date range filter ---
  presetThisMonth: string;
  presetLastMonth: string;
  presetLast30Days: string;
  presetThisQuarter: string;
  presetLastQuarter: string;
  presetThisYear: string;
  presetLastYear: string;
  clearDateRange: string;
  selectDateRange: string;
  noTransactionsInRange: string;
}
