import { ChangeDetectionStrategy, Component, inject, input, output } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { AppSettingsService } from '@core/services/app-settings.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { EmptyStateComponent } from '@shared/components/empty-state/empty-state.component';
import { AccountSummary } from '@shared/models/report.model';

@Component({
  selector: 'app-account-grid',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule, MatIconModule, CurrencyPipe, EmptyStateComponent],
  template: `
    @if (accounts().length > 0) {
      <div class="account-grid">
        @for (acc of accounts(); track acc.accountId) {
          <mat-card class="account-card" (click)="accountClick.emit(acc.accountId)">
            <mat-card-header>
              <div class="card-icon-wrap" mat-card-avatar>
                <mat-icon>account_balance</mat-icon>
              </div>
              <mat-card-title>{{ refData.getAccountLabel(acc.accountId) }}</mat-card-title>
              <mat-card-subtitle>{{ acc.transactionCount }} {{ settings.labels().transactionCountSuffix }}</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <p class="balance-amount"
                 [class.text-income]="acc.net >= 0"
                 [class.text-expense]="acc.net < 0">
                {{ acc.net | currency: 'EUR':'symbol':'1.2-2' }}
              </p>
            </mat-card-content>
          </mat-card>
        }
      </div>
    } @else {
      <app-empty-state icon="account_balance"
                       [message]="settings.labels().noAccountsEmpty" />
    }
  `,
  styles: `
    .account-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: var(--spc-16);
    }
    .account-card {
      cursor: pointer;
    }
    .card-icon-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
      width: var(--spc-40);
      height: var(--spc-40);
      border-radius: var(--rad-lg);
      background: var(--brand-surface);
      color: var(--brand-primary-light);
    }
    .balance-amount {
      font-size: var(--font-xl);
      font-weight: var(--fw-semibold);
      margin: var(--spc-12) 0 0;
    }
  `,
})
export class AccountGridComponent {
  readonly refData = inject(ReferenceDataService);
  readonly settings = inject(AppSettingsService);

  accounts = input.required<AccountSummary[]>();
  accountClick = output<string>();
}
