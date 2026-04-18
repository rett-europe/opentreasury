/**
 * Mock HTTP interceptor for offline development.
 * Intercepts /api/* requests and returns mock data when environment.useMocks is true.
 */
import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of } from 'rxjs';
import { environment } from '@env/environment';
import {
  MOCK_ACCOUNTS,
  MOCK_AUDIT,
  MOCK_CATEGORIES,
  MOCK_REFERENCE_DATA,
  MOCK_REPORT_BY_ACCOUNT,
  MOCK_REPORT_BALANCE,
  MOCK_REPORT_BY_CATEGORY,
  MOCK_REPORT_MONTHLY,
  MOCK_REPORT_SUMMARY,
  MOCK_TAGS,
  MOCK_TRANSACTIONS,
  MOCK_USER,
} from './mock-data';
import { Transaction, PaginatedResponse } from '@shared/models/transaction.model';

function randomDelay(): number {
  return 200 + Math.floor(Math.random() * 300);
}

function log(method: string, url: string, status: number, extra?: string): void {
  console.log(`[MOCK API] ${method} ${url} → ${status}${extra ? ` (${extra})` : ''}`);
}

function json<T>(body: T, status = 200) {
  return new HttpResponse<T>({ body, status });
}

function noContent() {
  return new HttpResponse<void>({ status: 204 });
}

/**
 * Functional interceptor — only active when useMocks is enabled.
 */
export const mockApiInterceptor: HttpInterceptorFn = (req, next) => {
  if (!(environment as Record<string, unknown>)['useMocks']) {
    return next(req);
  }

  const url = req.url;
  const method = req.method;

  // Only intercept API calls
  if (!url.includes('/api/')) {
    return next(req);
  }

  // Strip base URL to get the path (e.g. "/api/transactions"), without query params
  const pathWithParams = url.substring(url.indexOf('/api'));
  const path = pathWithParams.split('?')[0];

  // ---- User ----
  if (path === '/api/me' && method === 'GET') {
    log(method, path, 200);
    return of(json(MOCK_USER)).pipe(delay(randomDelay()));
  }

  if (path === '/api/me/preferences' && method === 'GET') {
    log(method, path, 200);
    return of(json({ language: 'es', theme: 'light', compactMode: false, reducedMotion: false })).pipe(delay(randomDelay()));
  }

  if (path === '/api/me/preferences' && method === 'PUT') {
    log(method, path, 200);
    return of(json(req.body)).pipe(delay(randomDelay()));
  }

  // ---- Reference data ----
  if (path === '/api/reference-data' && method === 'GET') {
    log(method, path, 200);
    return of(json(MOCK_REFERENCE_DATA)).pipe(delay(randomDelay()));
  }

  // ---- Transactions ----
  if (path === '/api/transactions' && method === 'GET') {
    const params = req.params;
    const year = params.get('year') ? Number(params.get('year')) : undefined;
    const month = params.get('month') ? Number(params.get('month')) : undefined;

    let items = [...MOCK_TRANSACTIONS];
    if (year) items = items.filter((t) => t.year === year);
    if (month) items = items.filter((t) => t.month === month);

    const accountIdFilter = params.get('accountId');
    if (accountIdFilter) items = items.filter((t) => t.accountId === accountIdFilter);
    const categoryIdFilter = params.get('categoryId');
    if (categoryIdFilter) items = items.filter((t) => t.categoryId === categoryIdFilter);
    const transactionTypeFilter = params.get('transactionType');
    if (transactionTypeFilter) items = items.filter((t) => t.transactionType === transactionTypeFilter);
    const categorizationStatusFilter = params.get('categorizationStatus');
    if (categorizationStatusFilter) items = items.filter((t) => t.categorizationStatus === categorizationStatusFilter);
    const reviewStatusFilter = params.get('reviewStatus');
    if (reviewStatusFilter) items = items.filter((t) => t.reviewStatus === reviewStatusFilter);

    const income = items.filter((t) => t.amount > 0).reduce((s, t) => s + t.amount, 0);
    const expenses = items.filter((t) => t.amount < 0).reduce((s, t) => s + Math.abs(t.amount), 0);

    const body: PaginatedResponse<Transaction> = {
      items,
      continuationToken: null,
      totalIncome: income,
      totalExpenses: expenses,
      net: income - expenses,
      transactionCount: items.length,
      uncategorizedCount: items.filter((t) => !t.categoryId).length,
    };
    log(method, path, 200, `${items.length} items`);
    return of(json(body)).pipe(delay(randomDelay()));
  }

  if (path.match(/^\/api\/transactions\/[^/]+$/) && method === 'GET') {
    const id = path.split('/').pop()!;
    const found = MOCK_TRANSACTIONS.find((t) => t.id === id);
    if (found) {
      log(method, path, 200);
      return of(json(found)).pipe(delay(randomDelay()));
    }
    log(method, path, 404);
    return of(new HttpResponse({ status: 404, body: { detail: 'Not found' } })).pipe(delay(randomDelay()));
  }

  if (path === '/api/transactions' && method === 'POST') {
    const body = req.body as Record<string, unknown>;
    const created = {
      id: `tx-mock-${Date.now()}`,
      type: 'transaction',
      ...body,
      createdBy: 'mock-oid-pedro',
      createdByName: 'Demo Admin',
      createdAt: new Date().toISOString(),
      updatedBy: null,
      updatedByName: null,
      updatedAt: null,
      isDeleted: false,
    };
    log(method, path, 201);
    return of(json(created, 201)).pipe(delay(randomDelay()));
  }

  if (path.match(/^\/api\/transactions\/[^/]+$/) && method === 'PUT') {
    const body = req.body as Record<string, unknown>;
    const id = path.split('/').pop()!;
    const existing = MOCK_TRANSACTIONS.find((t) => t.id === id);
    const updated = { ...(existing ?? {}), ...body, id, updatedAt: new Date().toISOString() };
    log(method, path, 200);
    return of(json(updated)).pipe(delay(randomDelay()));
  }

  if (path.match(/^\/api\/transactions\/[^/]+$/) && method === 'DELETE') {
    log(method, path, 204);
    return of(noContent()).pipe(delay(randomDelay()));
  }

  // ---- Transaction review (PATCH) ----
  if (path.match(/^\/api\/transactions\/[^/]+\/review$/) && method === 'PATCH') {
    const segments = path.split('/');
    const id = segments[segments.length - 2];
    const existing = MOCK_TRANSACTIONS.find((t) => t.id === id);
    const body = req.body as Record<string, unknown>;
    const updated = {
      ...(existing ?? {}),
      reviewStatus: body['reviewStatus'],
      reviewedBy: 'mock-oid-pedro',
      reviewedByName: 'Demo Admin',
      reviewedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    log(method, path, 200);
    return of(json(updated)).pipe(delay(randomDelay()));
  }

  // ---- Transaction categorize (PATCH) ----
  if (path.match(/^\/api\/transactions\/[^/]+\/categorize$/) && method === 'PATCH') {
    const segments = path.split('/');
    const id = segments[segments.length - 2];
    const existing = MOCK_TRANSACTIONS.find((t) => t.id === id);
    const body = req.body as Record<string, unknown>;
    const newCategoryId = body['categoryId'] as string | null;
    const updated = {
      ...(existing ?? {}),
      categoryId: newCategoryId,
      subcategoryId: body['subcategoryId'] as string | null,
      categorizationStatus: newCategoryId ? 'manually_categorized' : 'uncategorized',
      updatedAt: new Date().toISOString(),
    };
    log(method, path, 200);
    return of(json(updated)).pipe(delay(randomDelay()));
  }

  // ---- Transaction notes (POST) ----
  if (path.match(/^\/api\/transactions\/[^/]+\/notes$/) && method === 'POST') {
    const segments = path.split('/');
    const id = segments[segments.length - 2];
    const existing = MOCK_TRANSACTIONS.find((t) => t.id === id);
    const body = req.body as Record<string, unknown>;
    const note = {
      id: `note-mock-${Date.now()}`,
      text: body['text'] as string,
      author: 'mock-oid-pedro',
      authorName: 'Demo Admin',
      createdAt: new Date().toISOString(),
    };
    const updated = {
      ...(existing ?? {}),
      notes: [...(existing?.notes ?? []), note],
      updatedAt: new Date().toISOString(),
    };
    log(method, path, 200);
    return of(json(updated)).pipe(delay(randomDelay()));
  }

  // ---- Categories ----
  if (path === '/api/categories' && method === 'GET') {
    log(method, path, 200, `${MOCK_CATEGORIES.length} items`);
    return of(json(MOCK_CATEGORIES)).pipe(delay(randomDelay()));
  }

  if (path === '/api/categories' && method === 'POST') {
    const body = req.body as Record<string, unknown>;
    const created = { id: `cat-mock-${Date.now()}`, type: 'category', subcategories: [], ...body, createdAt: new Date().toISOString(), updatedAt: null };
    log(method, path, 201);
    return of(json(created, 201)).pipe(delay(randomDelay()));
  }

  if (path.match(/^\/api\/categories\/[^/]+$/) && method === 'PUT') {
    const body = req.body as Record<string, unknown>;
    const id = path.split('/').pop()!;
    const existing = MOCK_CATEGORIES.find((c) => c.id === id);
    const updated = { ...(existing ?? {}), ...body, id, updatedAt: new Date().toISOString() };
    log(method, path, 200);
    return of(json(updated)).pipe(delay(randomDelay()));
  }

  if (path.match(/^\/api\/categories\/[^/]+$/) && method === 'DELETE') {
    log(method, path, 204);
    return of(noContent()).pipe(delay(randomDelay()));
  }

  // ---- Accounts ----
  if (path === '/api/accounts' && method === 'GET') {
    log(method, path, 200, `${MOCK_ACCOUNTS.length} items`);
    return of(json(MOCK_ACCOUNTS)).pipe(delay(randomDelay()));
  }

  if (path === '/api/accounts' && method === 'POST') {
    const body = req.body as Record<string, unknown>;
    const created = { id: `acc-mock-${Date.now()}`, type: 'bank_account', ...body, createdAt: new Date().toISOString(), updatedAt: null };
    log(method, path, 201);
    return of(json(created, 201)).pipe(delay(randomDelay()));
  }

  // ---- Tags ----
  if (path === '/api/tags' && method === 'GET') {
    log(method, path, 200, `${MOCK_TAGS.length} items`);
    return of(json(MOCK_TAGS)).pipe(delay(randomDelay()));
  }

  if (path === '/api/tags' && method === 'POST') {
    const body = req.body as Record<string, unknown>;
    const created = { id: `tag-mock-${Date.now()}`, type: 'tag', ...body, createdAt: new Date().toISOString(), updatedAt: null };
    log(method, path, 201);
    return of(json(created, 201)).pipe(delay(randomDelay()));
  }

  // ---- Reports ----
  if (path === '/api/reports/summary' && method === 'GET') {
    log(method, path, 200);
    return of(json({
      year: 2026,
      totalIncome: MOCK_REPORT_SUMMARY.totalIncome,
      totalExpense: MOCK_REPORT_SUMMARY.totalExpenses,
      net: MOCK_REPORT_SUMMARY.net,
    })).pipe(delay(randomDelay()));
  }

  if (path === '/api/reports/by-category' && method === 'GET') {
    const year = Number(req.params.get('year')) || 2026;
    log(method, path, 200);
    return of(json({ year, items: MOCK_REPORT_BY_CATEGORY })).pipe(delay(randomDelay()));
  }

  if (path === '/api/reports/balance' && method === 'GET') {
    const year = Number(req.params.get('year')) || 2026;
    log(method, path, 200);
    return of(json({ year, items: MOCK_REPORT_BALANCE })).pipe(delay(randomDelay()));
  }

  if (path === '/api/reports/monthly-trend' && method === 'GET') {
    const year = Number(req.params.get('year')) || 2026;
    log(method, path, 200);
    return of(json({ year, months: MOCK_REPORT_MONTHLY })).pipe(delay(randomDelay()));
  }

  if (path === '/api/reports/by-account' && method === 'GET') {
    const year = Number(req.params.get('year')) || 2026;
    log(method, path, 200);
    return of(json({ year, items: MOCK_REPORT_BY_ACCOUNT })).pipe(delay(randomDelay()));
  }

  // ---- Import ----
  if (path === '/api/imports/preview' && method === 'POST') {
    const accountId = req.params.get('accountId') || 'acc-unicaja-01';
    const sheet = req.params.get('sheet');
    const account = MOCK_ACCOUNTS.find(a => a.id === accountId);

    // Discovery call (no `sheet`) → ask the user to pick one.
    if (!sheet) {
      const discovery = {
        requiresSheetSelection: true,
        candidateSheets: [
          { name: 'Movimientos 2026', dataRowCount: 52, headerRow: 6 },
          { name: 'Movimientos 2025', dataRowCount: 247, headerRow: 6 },
        ],
        ignoredSheets: [
          { name: 'Resumen', reason: 'missing_required_headers', missing: ['date', 'amount'] },
          { name: 'Notas', reason: 'empty' },
        ],
        account: {
          id: accountId,
          label: account?.accountLabel ?? 'Unknown',
          iban: account?.iban ?? '',
        },
        valid: false,
        importMode: 'full',
        errors: [],
        warnings: [],
        totalRows: 0,
        rowsWithErrors: 0,
        newCategories: [],
        newSubcategories: [],
        transactionsToImport: 0,
        duplicatesToSkip: 0,
        duplicateRows: [],
        selectedSheet: null,
        availableSheets: ['Movimientos 2026', 'Movimientos 2025'],
      };
      log(method, path, 200, 'sheet selection required');
      return of(json(discovery)).pipe(delay(randomDelay()));
    }

    const mockPreview = {
      valid: true,
      importMode: 'inline',
      errors: [],
      warnings: [],
      totalRows: 25,
      rowsWithErrors: 0,
      account: {
        id: accountId,
        label: account?.accountLabel ?? 'Unknown',
        iban: account?.iban ?? '',
      },
      newCategories: [
        { name: 'Donaciones', suggestedType: 'expense' },
        { name: 'Cuotas', suggestedType: 'expense' },
      ],
      newSubcategories: [{ categoryName: 'Donaciones', name: 'Donación Particular' }],
      transactionsToImport: 22,
      duplicatesToSkip: 3,
      duplicateRows: [
        { row: 5, date: '2026-01-15', amount: -45.00, description: 'RECIBO LUZ ENDESA' },
        { row: 12, date: '2026-02-01', amount: -120.50, description: 'TRANSFERENCIA ALQUILER' },
        { row: 18, date: '2026-02-15', amount: 1500.00, description: 'NOMINA EMPRESA XYZ' },
      ],
      requiresSheetSelection: false,
      selectedSheet: sheet,
      availableSheets: ['Movimientos 2026', 'Movimientos 2025'],
      ignoredSheets: [],
      candidateSheets: [],
    };
    log(method, path, 200);
    return of(json(mockPreview)).pipe(delay(randomDelay()));
  }

  if (path === '/api/imports/workbook' && method === 'POST') {
    const accountId = req.params.get('accountId') || 'acc-unicaja-01';
    const sheet = req.params.get('sheet');
    const account = MOCK_ACCOUNTS.find(a => a.id === accountId);
    const mockSummary = {
      importBatchId: 'mock-batch-' + Date.now(),
      importMode: 'inline',
      importSource: 'excel-inline',
      accountId,
      accountLabel: account?.accountLabel ?? 'Unknown',
      selectedSheet: sheet ?? 'Movimientos 2026',
      categoriesCreated: 2,
      subcategoriesAdded: 1,
      transactionsImported: 22,
      duplicatesSkipped: 3,
      rowsSkipped: 0,
      warnings: [],
    };
    log(method, path, 200);
    return of(json(mockSummary)).pipe(delay(randomDelay()));
  }

  // ---- Export ----
  if (path.startsWith('/api/export') && method === 'GET') {
    log(method, path, 200, 'empty blob');
    const blob = new Blob([''], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    return of(new HttpResponse({ status: 200, body: blob })).pipe(delay(randomDelay()));
  }

  // ---- Audit ----
  if (path === '/api/audit' && method === 'GET') {
    log(method, path, 200, `${MOCK_AUDIT.length} items`);
    return of(json({ items: MOCK_AUDIT, continuationToken: null })).pipe(delay(randomDelay()));
  }

  // ---- Fallthrough ----
  console.warn(`[MOCK API] Unhandled: ${method} ${path} — passing through`);
  return next(req);
};
