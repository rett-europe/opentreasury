import { ChangeDetectionStrategy, Component, ElementRef, inject, OnDestroy, OnInit, signal, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { fromEvent, Subject } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { AuthService } from '@core/auth/auth.service';
import { AppSettingsService } from '@core/services/app-settings.service';
import { TransactionService } from '@core/services/transaction.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { Transaction, TransactionType, TransactionQueryParams, ReviewStatus, CategorizationStatus } from '@shared/models/transaction.model';
import { PageHeaderComponent } from '@shared/components/page-header/page-header.component';
import { LoadingContainerComponent } from '@shared/components/loading-container/loading-container.component';
import { EmptyStateComponent } from '@shared/components/empty-state/empty-state.component';
import { StatusBadgeComponent } from '@shared/components/status-badge/status-badge.component';
import { TypeIconPipe } from '@shared/pipes/type-icon.pipe';
import { TypeColorPipe } from '@shared/pipes/type-color.pipe';
import { TransactionFilterBarComponent, TransactionFilters } from './tx-filter-bar.component';
import { QuickCategorizeDialogComponent } from './quick-categorize-dialog.component';
import { SplitDialogComponent, SplitDialogData } from './split-dialog.component';

@Component({
  selector: 'app-transaction-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatDialogModule,
    CurrencyPipe,
    DatePipe,
    PageHeaderComponent,
    LoadingContainerComponent,
    EmptyStateComponent,
    StatusBadgeComponent,
    TypeIconPipe,
    TypeColorPipe,
    TransactionFilterBarComponent,
  ],
  template: `
    <div class="page-container">
      <div class="sticky-header">
        <app-page-header [title]="settings.labels().transactions">
          @if (authService.isAdmin()) {
            <button mat-fab extended color="primary"
                    (click)="router.navigate(['/transactions/new'])">
              <mat-icon>add</mat-icon>
              {{ settings.labels().newTransaction }}
            </button>
          }
        </app-page-header>

        <app-tx-filter-bar (filtersChanged)="onFiltersChanged($event)" />
      </div>

      <div class="scroll-area" #scrollContainer>

      <app-loading-container [loading]="loading()">
        @if (transactions().length > 0) {
          <div class="table-wrapper">
            <table mat-table [dataSource]="transactions()" class="full-width">
              <!-- Type column -->
              <ng-container matColumnDef="type">
                <th mat-header-cell *matHeaderCellDef class="col-type">{{ settings.labels().type }}</th>
                <td mat-cell *matCellDef="let tx" class="col-type">
                  <div class="type-cell">
                    <mat-icon [class]="tx | typeColor"
                              [matTooltip]="typeTooltip(tx)"
                              class="type-icon">
                      {{ tx | typeIcon }}
                    </mat-icon>
                    @if (tx.isSplit) {
                      <mat-icon class="split-icon"
                                [matTooltip]="settings.labels().splitIndicator(tx.splitCount)">
                        call_split
                      </mat-icon>
                    }
                  </div>
                </td>
              </ng-container>

              <ng-container matColumnDef="date">
                <th mat-header-cell *matHeaderCellDef>{{ settings.labels().date }}</th>
                <td mat-cell *matCellDef="let tx">{{ tx.date | date: 'dd/MM/yyyy' }}</td>
              </ng-container>

              <ng-container matColumnDef="account">
                <th mat-header-cell *matHeaderCellDef>{{ settings.labels().account }}</th>
                <td mat-cell *matCellDef="let tx">{{ refData.getAccountLabel(tx.accountId) }}</td>
              </ng-container>

              <ng-container matColumnDef="bankDescription">
                <th mat-header-cell *matHeaderCellDef>{{ settings.labels().notes }}</th>
                <td mat-cell *matCellDef="let tx" class="description-cell"
                    [matTooltip]="tx.bankDescription || ''">
                  {{ tx.bankDescription || tx.detail || '—' }}
                </td>
              </ng-container>

              <!-- Category column — with uncategorized handling -->
              <ng-container matColumnDef="category">
                <th mat-header-cell *matHeaderCellDef>{{ settings.labels().category }}</th>
                <td mat-cell *matCellDef="let tx">
                  @if (tx.isSplit) {
                    <span class="split-label" role="button" tabindex="0"
                          (click)="toggleSplitExpand(tx); $event.stopPropagation()"
                          (keydown.enter)="toggleSplitExpand(tx); $event.stopPropagation()"
                          (keydown.space)="toggleSplitExpand(tx); $event.stopPropagation()">
                      {{ settings.labels().splitIndicator(tx.splitCount) }}
                    </span>
                  } @else if (tx.categoryId) {
                    {{ refData.getCategoryName(tx.categoryId) }}
                  } @else {
                    <span class="uncategorized-label">{{ settings.labels().uncategorizedLabel }}</span>
                    <button mat-icon-button class="categorize-btn"
                            [matTooltip]="settings.labels().quickCategorize"
                            (click)="openQuickCategorize(tx); $event.stopPropagation()">
                      <mat-icon class="categorize-icon">label</mat-icon>
                    </button>
                  }
                </td>
              </ng-container>

              <ng-container matColumnDef="subcategory">
                <th mat-header-cell *matHeaderCellDef>{{ settings.labels().subcategory }}</th>
                <td mat-cell *matCellDef="let tx">
                  @if (tx.categoryId && tx.subcategoryId) {
                    {{ refData.getSubcategoryName(tx.categoryId, tx.subcategoryId) }}
                  } @else {
                    —
                  }
                </td>
              </ng-container>

              <ng-container matColumnDef="tags">
                <th mat-header-cell *matHeaderCellDef>{{ settings.labels().tags }}</th>
                <td mat-cell *matCellDef="let tx">
                  <div class="tag-list">
                    @for (tagId of tx.tagIds; track tagId) {
                      <span class="tag-pill"
                            [style.background-color]="refData.getTagColor(tagId)"
                            [style.color]="refData.getTagTextColor(tagId)">
                        {{ refData.getTagName(tagId) }}
                      </span>
                    }
                  </div>
                </td>
              </ng-container>

              <ng-container matColumnDef="amount">
                <th mat-header-cell *matHeaderCellDef class="text-right">{{ settings.labels().amount }}</th>
                <td mat-cell *matCellDef="let tx" class="text-right"
                    [class]="tx | typeColor">
                  {{ tx.amount | currency: 'EUR':'symbol':'1.2-2' }}
                </td>
              </ng-container>

              <!-- Status column — uses StatusBadgeComponent -->
              <ng-container matColumnDef="status">
                <th mat-header-cell *matHeaderCellDef class="col-status">{{ settings.labels().reviewStatus }}</th>
                <td mat-cell *matCellDef="let tx" class="col-status">
                  <div class="status-badges">
                    <app-status-badge [status]="tx.reviewStatus" />
                    @if (!tx.categoryId && !tx.isSplit) {
                      <app-status-badge status="uncategorized" />
                    }
                  </div>
                </td>
              </ng-container>

              <ng-container matColumnDef="actions">
                <th mat-header-cell *matHeaderCellDef></th>
                <td mat-cell *matCellDef="let tx">
                  @if (authService.isAdmin()) {
                    <button mat-icon-button
                            [matTooltip]="tx.isSplit ? settings.labels().editSplit : settings.labels().splitTransaction"
                            (click)="openSplitDialog(tx); $event.stopPropagation()">
                      <mat-icon>call_split</mat-icon>
                    </button>
                  }
                  <button mat-icon-button
                          (click)="router.navigate(['/transactions', tx.id, 'edit'], { queryParams: { year: tx.year, month: tx.month } }); $event.stopPropagation()">
                    <mat-icon>edit</mat-icon>
                  </button>
                  <button mat-icon-button color="warn"
                          (click)="deleteTransaction(tx); $event.stopPropagation()">
                    <mat-icon>delete</mat-icon>
                  </button>
                </td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns; sticky: true"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns"
                  (click)="onRowClick(row)"></tr>
            </table>

            <!-- Expanded split lines shown below the table for expanded transactions -->
            @for (tx of transactions(); track tx.id) {
              @if (tx.isSplit && expandedSplitIds().has(tx.id)) {
                <div class="split-detail-panel">
                  <div class="split-detail-header">
                    {{ tx.bankDescription || tx.detail || '—' }} — {{ settings.labels().splitIndicator(tx.splitCount) }}
                  </div>
                  @for (line of tx.splitLines; track line.id) {
                    <div class="split-detail-line">
                      <span class="sdl-indicator">├─</span>
                      <span class="sdl-amount" [class.income-amount]="tx.amount > 0"
                            [class.expense-amount]="tx.amount < 0">
                        {{ line.amount | currency: 'EUR':'symbol':'1.2-2' }}
                      </span>
                      <span class="sdl-category">
                        @if (line.categoryId) {
                          {{ refData.getCategoryName(line.categoryId) }}
                          @if (line.subcategoryId) {
                            / {{ refData.getSubcategoryName(line.categoryId, line.subcategoryId) }}
                          }
                        } @else {
                          —
                        }
                      </span>
                      @if (line.detail) {
                        <span class="sdl-detail">"{{ line.detail }}"</span>
                      }
                    </div>
                  }
                </div>
              }
            }
          </div>
          @if (loadingMore()) {
            <div class="loading-more">Loading more…</div>
          }
        } @else {
          <app-empty-state icon="receipt_long"
                           [message]="settings.labels().noTransactionsThisMonth" />
        }
      </app-loading-container>
      </div>
    </div>
  `,
  styles: `
    :host {
      display: block;
      height: calc(100vh - 64px - var(--spc-24) * 2);
      overflow: hidden;
    }
    .page-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }
    .sticky-header {
      flex-shrink: 0;
    }
    .scroll-area {
      flex: 1;
      overflow-y: auto;
      min-height: 0;
    }
    .table-wrapper {
      background: var(--clr-surface);
      border-radius: var(--rad-lg);
      box-shadow: var(--elev-card);
      border: 1px solid var(--clr-border);
    }
    :host ::ng-deep .mat-mdc-header-row {
      background: var(--clr-surface);
    }
    .loading-more {
      text-align: center;
      padding: var(--spc-8);
      color: var(--clr-text-muted);
      font-size: var(--font-sm);
    }
    .text-right { text-align: right; }
    .description-cell {
      max-width: 250px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tag-list {
      display: flex;
      flex-wrap: wrap;
      gap: var(--spc-4);
    }
    .tag-pill {
      display: inline-block;
      padding: var(--spc-2) var(--spc-10);
      border-radius: var(--rad-pill);
      font-size: var(--font-xs);
      font-weight: var(--fw-medium);
      white-space: nowrap;
    }
    .col-type { width: 40px; text-align: center; }
    .col-status { width: 80px; }
    .type-icon {
      font-size: var(--font-lg);
      width: var(--font-lg);
      height: var(--font-lg);
    }
    .uncategorized-label {
      font-style: italic;
      color: var(--clr-text-disabled);
    }
    .categorize-btn {
      width: 24px;
      height: 24px;
      line-height: 24px;
    }
    .categorize-icon {
      font-size: var(--font-md);
      width: var(--font-md);
      height: var(--font-md);
      color: var(--clr-text-disabled);
    }
    .status-badges {
      display: flex;
      flex-direction: column;
      gap: var(--spc-2);
    }
    .type-cell {
      display: flex;
      align-items: center;
      gap: 2px;
    }
    .split-icon {
      font-size: 14px;
      width: 14px;
      height: 14px;
      color: var(--brand-primary);
    }
    .split-label {
      cursor: pointer;
      color: var(--brand-primary);
      font-weight: 500;
      font-size: var(--font-sm);
    }
    .split-label:hover {
      text-decoration: underline;
    }
    .split-detail-panel {
      background: var(--clr-surface-panel);
      border-left: 3px solid var(--brand-primary-muted);
      margin: 0 var(--spc-16, 16px) var(--spc-8, 8px) var(--spc-16, 16px);
      padding: var(--spc-8, 8px) var(--spc-12, 12px);
      border-radius: var(--rad-md, 8px);
      font-size: var(--font-sm, 14px);
    }
    .split-detail-header {
      font-weight: 600;
      color: var(--clr-text-secondary);
      margin-bottom: var(--spc-4, 4px);
      font-size: var(--font-xs, 12px);
    }
    .split-detail-line {
      display: flex;
      gap: var(--spc-8, 8px);
      align-items: center;
      padding: var(--spc-2, 2px) 0;
    }
    .sdl-indicator {
      color: var(--clr-text-disabled);
      font-family: monospace;
      flex-shrink: 0;
    }
    .sdl-amount {
      font-weight: 500;
      min-width: 80px;
      flex-shrink: 0;
    }
    .income-amount { color: var(--clr-income); }
    .expense-amount { color: var(--clr-expense); }
    .sdl-category {
      color: var(--clr-text-secondary);
    }
    .sdl-detail {
      color: var(--clr-text-muted);
      font-style: italic;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  `,
})
export class TransactionListComponent implements OnInit, OnDestroy {
  @ViewChild('scrollContainer', { static: true }) scrollContainer!: ElementRef<HTMLElement>;

  readonly router = inject(Router);
  readonly authService = inject(AuthService);
  readonly settings = inject(AppSettingsService);
  private readonly transactionService = inject(TransactionService);
  readonly refData = inject(ReferenceDataService);
  private readonly dialog = inject(MatDialog);
  private readonly destroy$ = new Subject<void>();

  readonly loading = signal(true);
  readonly loadingMore = signal(false);
  readonly expandedSplitIds = signal<Set<string>>(new Set());
  private allTransactions: Transaction[] = [];
  readonly transactions = signal<Transaction[]>([]);

  // Paging state — unified for both single-month and full-year
  private nextContinuationToken: string | null = null;
  private currentBaseParams: Record<string, unknown> | null = null;
  private currentMonth = 0;   // month currently being paged (1-12)
  private minMonth = 0;       // 1 for full year, same as currentMonth for single month
  private hasMore = false;

  private static readonly PAGE_SIZE = 100;

  readonly displayedColumns = [
    'type', 'date', 'account', 'bankDescription', 'category',
    'subcategory', 'tags', 'amount', 'status', 'actions',
  ];

  private currentFilters: TransactionFilters | null = null;

  ngOnInit(): void {
    this.refData.load();

    // Listen for scroll on the transaction scroll area
    const scrollEl = this.scrollContainer.nativeElement;
    fromEvent(scrollEl, 'scroll').pipe(
      filter(() => !this.loadingMore() && this.hasMore),
      takeUntil(this.destroy$),
    ).subscribe(() => {
      const nearBottom = scrollEl.scrollHeight - scrollEl.scrollTop - scrollEl.clientHeight < 300;
      if (nearBottom) {
        this.loadMore();
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onFiltersChanged(filters: TransactionFilters): void {
    this.currentFilters = filters;
    this.loadTransactions(filters);
  }

  typeTooltip(tx: Transaction): string {
    const labels = this.settings.labels();
    switch (tx.transactionType) {
      case 'income':   return labels.incomeOption;
      case 'expense':  return labels.expenseOption;
      case 'transfer': return tx.amount >= 0 ? labels.transferInOption : labels.transferOutOption;
      case 'refund':   return tx.amount >= 0 ? labels.refundReceivedOption : labels.refundGivenOption;
      default:         return '';
    }
  }

  openQuickCategorize(tx: Transaction): void {
    const dialogRef = this.dialog.open(QuickCategorizeDialogComponent, {
      width: '400px',
      data: { transaction: tx },
    });
    dialogRef.afterClosed().subscribe((updated: Transaction | undefined) => {
      if (updated) {
        const idx = this.allTransactions.findIndex(t => t.id === updated.id);
        if (idx >= 0) {
          this.allTransactions[idx] = { ...this.allTransactions[idx], ...updated };
        }
        this.applyClientFilters();
      }
    });
  }

  toggleSplitExpand(tx: Transaction): void {
    const current = new Set(this.expandedSplitIds());
    if (current.has(tx.id)) {
      current.delete(tx.id);
    } else {
      current.add(tx.id);
    }
    this.expandedSplitIds.set(current);
  }

  openSplitDialog(tx: Transaction): void {
    const dialogRef = this.dialog.open(SplitDialogComponent, {
      width: '900px',
      maxWidth: '95vw',
      data: { transaction: tx } as SplitDialogData,
    });
    dialogRef.afterClosed().subscribe((updated: Transaction | undefined) => {
      if (updated) {
        const idx = this.allTransactions.findIndex(t => t.id === updated.id);
        if (idx >= 0) {
          this.allTransactions[idx] = { ...this.allTransactions[idx], ...updated };
        }
        this.applyClientFilters();
      }
    });
  }

  onRowClick(tx: Transaction): void {
    if (tx.isSplit) {
      this.toggleSplitExpand(tx);
    } else {
      this.router.navigate(
        ['/transactions', tx.id, 'edit'],
        { queryParams: { year: tx.year, month: tx.month } },
      );
    }
  }

  // TODO: Replace native confirm() with MatDialog confirmation — tech debt
  deleteTransaction(tx: Transaction): void {
    if (confirm(this.settings.labels().deleteTransactionConfirm)) {
      this.transactionService.delete(tx.id, tx.year, tx.month).subscribe(() => {
        if (this.currentFilters) {
          this.loadTransactions(this.currentFilters);
        }
      });
    }
  }

  private loadTransactions(filters: TransactionFilters): void {
    this.loading.set(true);
    this.allTransactions = [];
    this.nextContinuationToken = null;

    const baseParams = {
      year: filters.year,
      accountId: filters.accountId || undefined,
      categoryId: filters.categoryId || undefined,
      subcategoryId: filters.subcategoryId || undefined,
      tagId: filters.tagId || undefined,
      transactionType: (filters.transactionType as TransactionType) || undefined,
      categorizationStatus: (filters.categorizationStatus as CategorizationStatus) || undefined,
      reviewStatus: (filters.reviewStatus as ReviewStatus) || undefined,
    };

    this.currentBaseParams = baseParams;

    if (filters.month) {
      // Single month: page through one month
      this.currentMonth = filters.month;
      this.minMonth = filters.month;
    } else {
      // Full year: start at month 12 (newest), walk down to 1
      this.currentMonth = 12;
      this.minMonth = 1;
    }

    this.hasMore = true;
    this.fetchPage(false);
  }

  /** Fetch one page (100 items) for the current month, then render. */
  private fetchPage(append: boolean): void {
    if (!this.currentBaseParams) return;
    if (append) {
      this.loadingMore.set(true);
    }

    const params: TransactionQueryParams = {
      ...this.currentBaseParams,
      month: this.currentMonth,
      pageSize: TransactionListComponent.PAGE_SIZE,
      continuationToken: this.nextContinuationToken ?? undefined,
    } as TransactionQueryParams;

    this.transactionService.list(params).pipe(takeUntil(this.destroy$)).subscribe({
      next: (res) => {
        if (res.continuationToken) {
          // More pages in this month
          this.nextContinuationToken = res.continuationToken;
          this.hasMore = true;
        } else if (this.currentMonth > this.minMonth) {
          // Month exhausted, advance to previous (older) month
          this.currentMonth--;
          this.nextContinuationToken = null;
          this.hasMore = true;
        } else {
          // All months exhausted
          this.nextContinuationToken = null;
          this.hasMore = false;
        }

        // If empty result and more months remain, skip to next month automatically
        if (res.items.length === 0 && this.hasMore) {
          this.fetchPage(append);
          return;
        }

        if (append) {
          this.appendResults(res.items);
        } else {
          this.applyResults(res.items);
        }
      },
      error: () => {
        this.hasMore = false;
        if (append) {
          this.loadingMore.set(false);
        } else {
          this.applyResults([]);
        }
      },
    });
  }

  private loadMore(): void {
    this.fetchPage(true);
  }

  private applyResults(items: Transaction[]): void {
    this.allTransactions = items;
    this.applyClientFilters();
    this.loading.set(false);
  }

  private appendResults(items: Transaction[]): void {
    this.allTransactions = [...this.allTransactions, ...items];
    this.applyClientFilters();
    this.loadingMore.set(false);
  }

  private applyClientFilters(): void {
    let filtered = this.allTransactions;
    const search = this.currentFilters?.search?.toLowerCase().trim();

    if (search) {
      filtered = filtered.filter(tx => {
        const fields = [
          tx.bankDescription,
          tx.detail,
          tx.categoryId ? this.refData.getCategoryName(tx.categoryId) : null,
          tx.categoryId && tx.subcategoryId ? this.refData.getSubcategoryName(tx.categoryId, tx.subcategoryId) : null,
          this.refData.getAccountLabel(tx.accountId),
          ...(tx.tagIds || []).map(id => this.refData.getTagName(id)),
          String(tx.amount),
        ];
        return fields.some(f => f && f.toLowerCase().includes(search));
      });
    }

    const amountMin = this.currentFilters?.amountMin;
    const amountMax = this.currentFilters?.amountMax;
    if (amountMin != null) {
      filtered = filtered.filter(tx => Math.abs(Number(tx.amount)) >= amountMin);
    }
    if (amountMax != null) {
      filtered = filtered.filter(tx => Math.abs(Number(tx.amount)) <= amountMax);
    }

    this.transactions.set(filtered);
  }
}
