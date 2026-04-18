import { ChangeDetectionStrategy, Component, computed, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatInputModule } from '@angular/material/input';
import { FormsModule } from '@angular/forms';
import { AppSettingsService } from '../../core/services/app-settings.service';
import { ReportService } from '../../core/services/report.service';
import { ReferenceDataService } from '../../core/services/reference-data.service';
import { BalanceItem } from '../../shared/models/report.model';
import { catchError, finalize, map, switchMap } from 'rxjs/operators';
import { of, Subject } from 'rxjs';

type SortField = 'categoryName' | 'subcategoryName' | 'income' | 'expense';
type SortDirection = 'asc' | 'desc';

interface BalanceFilters {
  category: string;
  subcategory: string;
  amount: string;
}

interface BalanceTableRow extends BalanceItem {
  showCategory: boolean;
  categoryRowSpan: number;
}

interface BalanceCategoryGroup {
  categoryId: string;
  categoryName: string;
  rows: BalanceItem[];
}

type BalanceKind = 'income' | 'expense';


@Component({
  selector: 'app-balance',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatSelectModule,
    MatFormFieldModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatInputModule,
    FormsModule,
  ],
  template: `
    <div class="balance-container">
      <div class="balance-hero">
        <div>
          <p class="eyebrow">{{ settings.labels().balance }}</p>
          <h1>{{ settings.labels().balance }}</h1>
          <p class="subtitle">{{ settings.labels().balanceSubtitle }}</p>
        </div>

        <mat-form-field appearance="outline" class="year-selector">
          <mat-label>{{ settings.labels().year }}</mat-label>
          <mat-select [(ngModel)]="selectedYear" (selectionChange)="loadBalance()">
            @for (year of availableYears; track year) {
              <mat-option [value]="year">
                {{ year }}
              </mat-option>
            }
          </mat-select>
        </mat-form-field>
      </div>

      @if (!loading()) {
        <div class="balance-summary-strip">
          <div class="summary-card income">
            <span class="summary-label">{{ settings.labels().totalIncome }}</span>
            <strong>{{ totalIncome() | currency:'EUR':'symbol':'1.2-2' }}</strong>
          </div>
          <div class="summary-card expense">
            <span class="summary-label">{{ settings.labels().totalExpenses }}</span>
            <strong>{{ totalExpense() | currency:'EUR':'symbol':'1.2-2' }}</strong>
          </div>
          <div class="summary-card balance">
            <span class="summary-label">{{ settings.labels().netBalance }}</span>
            <strong>{{ netBalance() | currency:'EUR':'symbol':'1.2-2' }}</strong>
          </div>
        </div>
      }

      @if (loading()) {
        <div class="loading-container">
          <mat-spinner diameter="44"></mat-spinner>
        </div>
      }

      @if (!loading()) {
        <div class="tables-grid">
        <section class="balance-panel income-panel">
          <div class="panel-header">
            <div>
              <h2>{{ settings.labels().totalIncome }}</h2>
              <p>{{ settings.labels().balanceVisibleRows(visibleIncomeRows().length) }}</p>
            </div>
          </div>

          <div class="filter-grid">
            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>{{ settings.labels().category }}</mat-label>
              <input matInput [(ngModel)]="incomeFilters.category" (ngModelChange)="refreshIncomeRows()"
                [placeholder]="settings.labels().balanceFilterCategoryPlaceholder">
            </mat-form-field>

            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>{{ settings.labels().subcategory }}</mat-label>
              <input matInput [(ngModel)]="incomeFilters.subcategory" (ngModelChange)="refreshIncomeRows()"
                [placeholder]="settings.labels().balanceFilterSubcategoryPlaceholder">
            </mat-form-field>

            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>{{ settings.labels().amount }}</mat-label>
              <input matInput [(ngModel)]="incomeFilters.amount" (ngModelChange)="refreshIncomeRows()"
                [placeholder]="settings.labels().balanceAmountPlaceholderIncome">
            </mat-form-field>
          </div>

          <div class="table-shell">
            <table class="balance-table">
              <thead>
                <tr>
                  <th>
                    <button type="button" class="sort-button" (click)="toggleSort('income', 'categoryName')">
                      {{ settings.labels().category }}
                      <mat-icon>{{ sortIcon('income', 'categoryName') }}</mat-icon>
                    </button>
                  </th>
                  <th>
                    <button type="button" class="sort-button" (click)="toggleSort('income', 'subcategoryName')">
                      {{ settings.labels().subcategory }}
                      <mat-icon>{{ sortIcon('income', 'subcategoryName') }}</mat-icon>
                    </button>
                  </th>
                  <th class="amount-col">
                    <button type="button" class="sort-button" (click)="toggleSort('income', 'income')">
                      {{ settings.labels().amount }}
                      <mat-icon>{{ sortIcon('income', 'income') }}</mat-icon>
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                @for (item of visibleIncomeRows(); track item.categoryId + ':' + (item.subcategoryId ?? '')) {
                  <tr>
                    @if (item.showCategory) {
                      <td [attr.rowspan]="item.categoryRowSpan" class="category-cell">
                        {{ item.categoryName }}
                      </td>
                    }
                    <td>{{ item.subcategoryName || '-' }}</td>
                    <td class="amount-cell income-text">{{ item.income | currency:'EUR':'symbol':'1.2-2' }}</td>
                  </tr>
                }
                @if (visibleIncomeRows().length === 0) {
                  <tr>
                    <td colspan="3" class="empty-state">{{ settings.labels().balanceNoIncomeMatches }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </section>

        <section class="balance-panel expense-panel">
          <div class="panel-header">
            <div>
              <h2>{{ settings.labels().totalExpenses }}</h2>
              <p>{{ settings.labels().balanceVisibleRows(visibleExpenseRows().length) }}</p>
            </div>
          </div>

          <div class="filter-grid">
            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>{{ settings.labels().category }}</mat-label>
              <input matInput [(ngModel)]="expenseFilters.category" (ngModelChange)="refreshExpenseRows()"
                [placeholder]="settings.labels().balanceFilterCategoryPlaceholder">
            </mat-form-field>

            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>{{ settings.labels().subcategory }}</mat-label>
              <input matInput [(ngModel)]="expenseFilters.subcategory" (ngModelChange)="refreshExpenseRows()"
                [placeholder]="settings.labels().balanceFilterSubcategoryPlaceholder">
            </mat-form-field>

            <mat-form-field appearance="outline" class="filter-field">
              <mat-label>{{ settings.labels().amount }}</mat-label>
              <input matInput [(ngModel)]="expenseFilters.amount" (ngModelChange)="refreshExpenseRows()"
                [placeholder]="settings.labels().balanceAmountPlaceholderExpense">
            </mat-form-field>
          </div>

          <div class="table-shell">
            <table class="balance-table">
              <thead>
                <tr>
                  <th>
                    <button type="button" class="sort-button" (click)="toggleSort('expense', 'categoryName')">
                      {{ settings.labels().category }}
                      <mat-icon>{{ sortIcon('expense', 'categoryName') }}</mat-icon>
                    </button>
                  </th>
                  <th>
                    <button type="button" class="sort-button" (click)="toggleSort('expense', 'subcategoryName')">
                      {{ settings.labels().subcategory }}
                      <mat-icon>{{ sortIcon('expense', 'subcategoryName') }}</mat-icon>
                    </button>
                  </th>
                  <th class="amount-col">
                    <button type="button" class="sort-button" (click)="toggleSort('expense', 'expense')">
                      {{ settings.labels().amount }}
                      <mat-icon>{{ sortIcon('expense', 'expense') }}</mat-icon>
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                @for (item of visibleExpenseRows(); track item.categoryId + ':' + (item.subcategoryId ?? '')) {
                  <tr>
                    @if (item.showCategory) {
                      <td [attr.rowspan]="item.categoryRowSpan" class="category-cell">
                        {{ item.categoryName }}
                      </td>
                    }
                    <td>{{ item.subcategoryName || '-' }}</td>
                    <td class="amount-cell expense-text">{{ item.expense | currency:'EUR':'symbol':'1.2-2' }}</td>
                  </tr>
                }
                @if (visibleExpenseRows().length === 0) {
                  <tr>
                    <td colspan="3" class="empty-state">{{ settings.labels().balanceNoExpenseMatches }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </section>
        </div>
      }
    </div>
  `,
  styles: [`
    .balance-container {
      padding: 24px;
      max-width: 1440px;
      margin: 0 auto;
      display: grid;
      gap: 24px;
    }

    .balance-hero {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      padding: 28px 32px;
      border-radius: 28px;
      background:
        radial-gradient(circle at top left, rgba(79, 140, 255, 0.18), transparent 34%),
        radial-gradient(circle at top right, rgba(47, 179, 128, 0.18), transparent 32%),
        linear-gradient(135deg, #f7f9fc 0%, #eef4ff 100%);
      border: 1px solid rgba(84, 112, 198, 0.12);
      box-shadow: 0 18px 50px rgba(31, 48, 94, 0.08);
    }

    .eyebrow {
      margin: 0 0 6px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.75rem;
      font-weight: 700;
      color: #4c63a6;
    }

    .balance-hero h1 {
      margin: 0;
      font-size: clamp(2rem, 2.8vw, 3rem);
      line-height: 1;
      font-weight: 700;
      color: #1d2c57;
    }

    .subtitle {
      margin: 10px 0 0;
      color: #556582;
      max-width: 56ch;
    }

    .year-selector {
      width: 140px;
    }

    .balance-summary-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
    }

    .summary-card {
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding: 18px 20px;
      border-radius: 22px;
      border: 1px solid rgba(16, 24, 40, 0.08);
      background: #fff;
      box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
    }

    .summary-card strong {
      font-size: 1.4rem;
      line-height: 1.1;
    }

    .summary-card.income {
      border-color: rgba(46, 125, 50, 0.16);
      background: linear-gradient(180deg, #ffffff 0%, #effaf1 100%);
    }

    .summary-card.expense {
      border-color: rgba(198, 40, 40, 0.16);
      background: linear-gradient(180deg, #ffffff 0%, #fff1f1 100%);
    }

    .summary-card.balance {
      border-color: rgba(59, 91, 219, 0.16);
      background: linear-gradient(180deg, #ffffff 0%, #eef3ff 100%);
    }

    .loading-container {
      display: flex;
      justify-content: center;
      padding: 56px;
    }

    .summary-label {
      color: #5f6f8d;
      font-size: 0.9rem;
      font-weight: 600;
    }

    .tables-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 20px;
      align-items: start;
    }

    .balance-panel {
      display: grid;
      gap: 16px;
      padding: 20px;
      border-radius: 28px;
      background: #ffffff;
      border: 1px solid rgba(16, 24, 40, 0.08);
      box-shadow: 0 18px 42px rgba(15, 23, 42, 0.07);
      overflow: hidden;
    }

    .income-panel {
      background:
        linear-gradient(180deg, rgba(240, 251, 244, 0.96) 0%, #ffffff 18%);
    }

    .expense-panel {
      background:
        linear-gradient(180deg, rgba(255, 243, 243, 0.96) 0%, #ffffff 18%);
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    .panel-header h2 {
      margin: 0;
      font-size: 1.35rem;
      color: #23324f;
    }

    .panel-header p {
      margin: 4px 0 0;
      color: #62708a;
      font-size: 0.95rem;
    }

    .filter-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .filter-field {
      width: 100%;
    }

    .table-shell {
      overflow: auto;
      border-radius: 22px;
      border: 1px solid rgba(16, 24, 40, 0.08);
      background: rgba(255, 255, 255, 0.92);
    }

    .balance-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      min-width: 540px;
    }

    .balance-table th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: #f7f9fc;
      border-bottom: 1px solid rgba(16, 24, 40, 0.08);
      text-align: left;
      padding: 0;
    }

    .balance-table td {
      padding: 14px 16px;
      border-bottom: 1px solid rgba(16, 24, 40, 0.06);
      color: #23324f;
      background: rgba(255, 255, 255, 0.92);
    }

    .balance-table tbody tr:hover td {
      background: #f8fbff;
    }

    .sort-button {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      border: 0;
      background: transparent;
      padding: 14px 16px;
      font: inherit;
      font-weight: 700;
      color: #243451;
      cursor: pointer;
    }

    .sort-button mat-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
      color: #70809c;
    }

    .category-cell {
      font-weight: 700;
      color: #1f3058;
      background:
        linear-gradient(180deg, rgba(242, 246, 252, 0.9) 0%, rgba(248, 250, 253, 0.9) 100%) !important;
      border-right: 1px solid rgba(16, 24, 40, 0.06);
      vertical-align: middle;
      min-width: 160px;
    }

    .amount-col,
    .amount-cell {
      text-align: right;
    }

    .amount-cell {
      font-variant-numeric: tabular-nums;
      font-weight: 700;
    }

    .income-text {
      color: #1f7a37;
    }

    .expense-text {
      color: #be2f2f;
    }

    .empty-state {
      text-align: center;
      color: #6f7f99;
      padding: 28px 16px !important;
    }

    @media (max-width: 1100px) {
      .tables-grid,
      .balance-summary-strip,
      .filter-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 720px) {
      .balance-container {
        padding: 16px;
      }

      .balance-hero {
        padding: 22px;
        align-items: stretch;
        flex-direction: column;
      }
    }
  `],
})
export class BalanceComponent implements OnInit {
  public readonly settings = inject(AppSettingsService);
  private readonly reportService = inject(ReportService);
  private readonly referenceDataService = inject(ReferenceDataService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly yearChange$ = new Subject<number>();

  selectedYear = new Date().getFullYear();
  availableYears = this.generateAvailableYears();
  loading = signal(false);
  incomeData = signal<BalanceItem[]>([]);
  expenseData = signal<BalanceItem[]>([]);
  totalIncome = signal(0);
  totalExpense = signal(0);
  readonly netBalance = computed(() => this.totalIncome() - this.totalExpense());

  incomeFilters: BalanceFilters = {
    category: '',
    subcategory: '',
    amount: '',
  };

  expenseFilters: BalanceFilters = {
    category: '',
    subcategory: '',
    amount: '',
  };

  private readonly incomeSort = signal<{ field: SortField; direction: SortDirection }>({
    field: 'categoryName',
    direction: 'asc',
  });

  private readonly expenseSort = signal<{ field: SortField; direction: SortDirection }>({
    field: 'categoryName',
    direction: 'asc',
  });

  readonly visibleIncomeRows = signal<BalanceTableRow[]>([]);
  readonly visibleExpenseRows = signal<BalanceTableRow[]>([]);

  private generateAvailableYears(): number[] {
    const currentYear = new Date().getFullYear();
    const years: number[] = [];
    for (let year = currentYear - 5; year <= currentYear; year++) {
      years.push(year);
    }
    return years;
  }

  loadBalance() {
    this.yearChange$.next(this.selectedYear);
  }

  private processBalanceItems(items: BalanceItem[]): {
    incomeRows: BalanceItem[];
    expenseRows: BalanceItem[];
    totalIncome: number;
    totalExpense: number;
  } {
    const coerce = (items: BalanceItem[]): BalanceItem[] =>
      items.map(i => ({ ...i, income: +i.income, expense: +i.expense, net: +i.net }));

    const coerced = coerce(items);

    const incomeRows = coerced
      .filter(item => item.income > 0)
      .sort((a, b) => {
        if (a.categoryName !== b.categoryName) {
          return a.categoryName.localeCompare(b.categoryName);
        }
        return (a.subcategoryName || '').localeCompare(b.subcategoryName || '');
      });

    const expenseRows = coerced
      .filter(item => item.expense > 0)
      .sort((a, b) => {
        if (a.categoryName !== b.categoryName) {
          return a.categoryName.localeCompare(b.categoryName);
        }
        return (a.subcategoryName || '').localeCompare(b.subcategoryName || '');
      });

    const totalIncome = incomeRows.reduce((sum, item) => sum + item.income, 0);
    const totalExpense = expenseRows.reduce((sum, item) => sum + item.expense, 0);

    return { incomeRows, expenseRows, totalIncome, totalExpense };
  }

  refreshIncomeRows(): void {
    this.visibleIncomeRows.set(this.buildDisplayRows('income', this.incomeData(), this.incomeFilters, this.incomeSort()));
  }

  refreshExpenseRows(): void {
    this.visibleExpenseRows.set(this.buildDisplayRows('expense', this.expenseData(), this.expenseFilters, this.expenseSort()));
  }

  toggleSort(kind: 'income' | 'expense', field: SortField): void {
    const sortSignal = kind === 'income' ? this.incomeSort : this.expenseSort;
    const current = sortSignal();

    sortSignal.set({
      field,
      direction: current.field === field && current.direction === 'asc' ? 'desc' : 'asc',
    });

    if (kind === 'income') {
      this.refreshIncomeRows();
      return;
    }

    this.refreshExpenseRows();
  }

  sortIcon(kind: 'income' | 'expense', field: SortField): string {
    const current = kind === 'income' ? this.incomeSort() : this.expenseSort();
    if (current.field !== field) {
      return 'unfold_more';
    }
    return current.direction === 'asc' ? 'arrow_upward' : 'arrow_downward';
  }

  private buildDisplayRows(
    kind: BalanceKind,
    rows: BalanceItem[],
    filters: BalanceFilters,
    sort: { field: SortField; direction: SortDirection },
  ): BalanceTableRow[] {
    const amountFilter = filters.amount.trim().replace(',', '.');

    const filtered = rows.filter((row) => {
      const categoryMatch = row.categoryName.toLowerCase().includes(filters.category.trim().toLowerCase());
      const subcategoryMatch = (row.subcategoryName || '-').toLowerCase().includes(filters.subcategory.trim().toLowerCase());
      const value = kind === 'expense' ? row.expense : row.income;
      const amountMatch = amountFilter === '' || value.toFixed(2).includes(amountFilter);
      return categoryMatch && subcategoryMatch && amountMatch;
    });

    const groupedRows = this.groupRowsByCategory(filtered);
    const sortedGroups = this.sortGroups(groupedRows, sort);
    const sortedRows = sortedGroups.flatMap((group) => this.sortRowsWithinGroup(group.rows, sort));

    return this.addCategoryGrouping(sortedRows, sort.field === 'categoryName');
  }

  private groupRowsByCategory(rows: BalanceItem[]): BalanceCategoryGroup[] {
    const grouped = new Map<string, BalanceCategoryGroup>();

    for (const row of rows) {
      const key = row.categoryId || row.categoryName;
      const current = grouped.get(key);

      if (current) {
        current.rows.push(row);
        continue;
      }

      grouped.set(key, {
        categoryId: row.categoryId,
        categoryName: row.categoryName,
        rows: [row],
      });
    }

    return Array.from(grouped.values());
  }

  private sortGroups(
    groups: BalanceCategoryGroup[],
    sort: { field: SortField; direction: SortDirection },
  ): BalanceCategoryGroup[] {
    const direction = sort.field === 'categoryName' && sort.direction === 'desc' ? -1 : 1;

    return [...groups].sort((left, right) => {
      const categoryCompare = left.categoryName.localeCompare(right.categoryName);
      if (categoryCompare !== 0) {
        return categoryCompare * direction;
      }

      return left.categoryId.localeCompare(right.categoryId);
    });
  }

  private sortRowsWithinGroup(
    rows: BalanceItem[],
    sort: { field: SortField; direction: SortDirection },
  ): BalanceItem[] {
    const direction = sort.direction === 'asc' ? 1 : -1;
    const fieldToSort: Exclude<SortField, 'categoryName'> =
      sort.field === 'categoryName' ? 'subcategoryName' : sort.field;

    return [...rows].sort((left, right) => {
      const primary = this.compareValue(left[fieldToSort], right[fieldToSort]) * direction;
      if (primary !== 0) {
        return primary;
      }

      const subcategoryCompare = (left.subcategoryName || '').localeCompare(right.subcategoryName || '');
      if (subcategoryCompare !== 0) {
        return subcategoryCompare;
      }

      return left.categoryId.localeCompare(right.categoryId);
    });
  }

  private compareValue(left: string | number | undefined, right: string | number | undefined): number {
    if (typeof left === 'number' && typeof right === 'number') {
      return left - right;
    }

    return String(left || '').localeCompare(String(right || ''));
  }

  private addCategoryGrouping(rows: BalanceItem[], mergeCategories: boolean): BalanceTableRow[] {
    if (!mergeCategories) {
      return rows.map((row) => ({
        ...row,
        showCategory: true,
        categoryRowSpan: 1,
      }));
    }

    const grouped = new Map<string, number>();
    for (const row of rows) {
      grouped.set(row.categoryId, (grouped.get(row.categoryId) || 0) + 1);
    }

    const seen = new Set<string>();
    return rows.map((row) => {
      const showCategory = !seen.has(row.categoryId);
      if (showCategory) {
        seen.add(row.categoryId);
      }

      return {
        ...row,
        showCategory,
        categoryRowSpan: showCategory ? grouped.get(row.categoryId) || 1 : 0,
      };
    });
  }

  ngOnInit() {
    // Fire-and-forget: ReferenceDataService.load() is a no-op if already cached,
    // and the balance API returns pre-resolved category names. Same pattern as
    // transaction-list and other consumers — no await needed.
    this.referenceDataService.load();

    // switchMap cancels in-flight requests on rapid year changes
    this.yearChange$.pipe(
      takeUntilDestroyed(this.destroyRef),
      switchMap(year => {
        this.loading.set(true);
        return this.reportService.getBalance(year).pipe(
          map((items: BalanceItem[]) => this.processBalanceItems(items)),
          catchError((error) => {
            console.error('Error loading balance data:', error);
            return of({ incomeRows: [], expenseRows: [], totalIncome: 0, totalExpense: 0 });
          }),
          finalize(() => this.loading.set(false)),
        );
      }),
    ).subscribe((result) => {
      this.incomeData.set(result.incomeRows);
      this.expenseData.set(result.expenseRows);
      this.totalIncome.set(result.totalIncome);
      this.totalExpense.set(result.totalExpense);
      this.refreshIncomeRows();
      this.refreshExpenseRows();
    });

    this.loadBalance();
  }
}
