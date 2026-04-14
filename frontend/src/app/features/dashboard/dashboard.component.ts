import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { forkJoin, catchError, of } from 'rxjs';
import { AuthService } from '@core/auth/auth.service';
import { AppSettingsService } from '@core/services/app-settings.service';
import { ReportService } from '@core/services/report.service';
import { TransactionService } from '@core/services/transaction.service';
import { TransactionSummary, AccountSummary } from '@shared/models/report.model';
import { Transaction } from '@shared/models/transaction.model';
import { PageHeaderComponent } from '@shared/components/page-header/page-header.component';
import { SectionTitleComponent } from '@shared/components/section-title/section-title.component';
import { LoadingContainerComponent } from '@shared/components/loading-container/loading-container.component';
import { EmptyStateComponent } from '@shared/components/empty-state/empty-state.component';
import { KpiStripComponent } from './kpi-strip.component';
import { AccountGridComponent } from './account-grid.component';
import { RecentTransactionsTableComponent } from './recent-transactions-table.component';

const DEFAULT_SUMMARY: TransactionSummary = { totalIncome: 0, totalExpenses: 0, net: 0 };

@Component({
  selector: 'app-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DatePipe, MatButtonModule, MatIconModule,
    PageHeaderComponent, SectionTitleComponent,
    LoadingContainerComponent, EmptyStateComponent,
    KpiStripComponent, AccountGridComponent,
    RecentTransactionsTableComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="settings.labels().dashboard"
                       [subtitle]="(today | date: 'longDate') ?? ''">
        @if (authService.isAdmin()) {
          <button mat-fab extended color="primary"
                  (click)="router.navigate(['/transactions/new'])">
            <mat-icon>add</mat-icon>
            {{ settings.labels().newTransaction }}
          </button>
        }
      </app-page-header>

      <app-loading-container [loading]="loading()">
        <app-section-title [text]="settings.labels().accountBalances" />
        <app-account-grid
          [accounts]="accountSummaries()"
          (accountClick)="onAccountClick($event)" />

        <app-section-title [text]="settings.labels().monthlySummary" />
        <app-kpi-strip [summary]="summary()" />

        <app-section-title [text]="settings.labels().recentTransactions" />
        @if (recentTransactions().length > 0) {
          <app-recent-transactions-table
            [transactions]="recentTransactions()"
            (rowClick)="onRowClick($event)"
            (viewAll)="router.navigate(['/transactions'])" />
        } @else {
          <app-empty-state icon="receipt_long"
                           [message]="settings.labels().noTransactionsThisMonth" />
        }
      </app-loading-container>
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  readonly authService = inject(AuthService);
  readonly router = inject(Router);
  readonly settings = inject(AppSettingsService);
  private readonly reportService = inject(ReportService);
  private readonly transactionService = inject(TransactionService);

  readonly today = new Date();
  readonly loading = signal(true);
  readonly summary = signal<TransactionSummary | null>(null);
  readonly accountSummaries = signal<AccountSummary[]>([]);
  readonly recentTransactions = signal<Transaction[]>([]);

  ngOnInit(): void {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;

    forkJoin({
      accounts: this.reportService.getByAccount(year).pipe(catchError(() => of([] as AccountSummary[]))),
      summary: this.reportService.getSummary(year, month).pipe(catchError(() => of(DEFAULT_SUMMARY))),
      transactions: this.transactionService.list({ year, month, pageSize: 10 }).pipe(
        catchError(() => of({ items: [] as Transaction[], continuationToken: null, totalIncome: 0, totalExpenses: 0, net: 0 })),
      ),
    }).subscribe(({ accounts, summary, transactions }) => {
      this.accountSummaries.set(accounts);
      this.summary.set(summary);
      this.recentTransactions.set(transactions.items);
      this.loading.set(false);
    });
  }

  onAccountClick(accountId: string): void {
    this.router.navigate(['/transactions'], { queryParams: { accountId } });
  }

  onRowClick(tx: Transaction): void {
    if (this.authService.isAdmin()) {
      this.router.navigate(['/transactions', tx.id, 'edit'], { queryParams: { year: tx.year, month: tx.month } });
    }
  }
}
