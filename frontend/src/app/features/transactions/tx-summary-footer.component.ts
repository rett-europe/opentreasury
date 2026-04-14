import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { inject } from '@angular/core';
import { AppSettingsService } from '@core/services/app-settings.service';

export interface TransactionSummaryData {
  totalIncome: number;
  totalExpenses: number;
  net: number;
  transactionCount: number;
  uncategorizedCount: number;
  transfersTotal: number;
}

@Component({
  selector: 'app-tx-summary-footer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CurrencyPipe],
  template: `
    @if (loading()) {
      <div class="summary-strip shimmer" aria-label="Loading summary…">
        <span class="shimmer-block"></span>
        <span class="shimmer-block"></span>
        <span class="shimmer-block wide"></span>
        <span class="shimmer-block wide"></span>
        <span class="shimmer-block wide"></span>
      </div>
    } @else {
      <div class="summary-strip">
        <span class="summary-item summary-count">
          {{ settings.labels().transactionCount(summary().transactionCount) }}
        </span>
        @if (summary().uncategorizedCount > 0) {
          <span class="summary-item uncategorized-count">
            {{ settings.labels().uncategorizedCount(summary().uncategorizedCount) }}
          </span>
        }
        <span class="summary-item type-income">
          {{ settings.labels().totalIncome }}: {{ summary().totalIncome | currency: 'EUR':'symbol':'1.2-2' }}
        </span>
        <span class="summary-item type-expense">
          {{ settings.labels().totalExpenses }}: {{ summary().totalExpenses | currency: 'EUR':'symbol':'1.2-2' }}
        </span>
        <span class="summary-item"
              [class.type-income]="summary().net >= 0"
              [class.type-expense]="summary().net < 0">
          {{ settings.labels().totalNet }}: {{ summary().net | currency: 'EUR':'symbol':'1.2-2' }}
        </span>
        @if (summary().transfersTotal !== 0) {
          <span class="summary-item type-transfer">
            {{ settings.labels().transfersTotal }}: {{ summary().transfersTotal | currency: 'EUR':'symbol':'1.2-2' }}
          </span>
        }
      </div>
    }
  `,
  styles: `
    .summary-strip {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: var(--spc-24);
      flex-wrap: wrap;
      padding: var(--spc-8) var(--spc-24);
      background: var(--clr-surface-panel);
      border-bottom: 1px solid var(--clr-border);
      font-weight: var(--fw-medium);
      font-size: var(--font-sm);
    }
    .summary-count {
      color: var(--clr-text-muted);
    }
    .uncategorized-count {
      color: var(--clr-warning);
    }
    .summary-strip.shimmer {
      gap: var(--spc-16);
    }
    .shimmer-block {
      display: inline-block;
      height: 14px;
      width: 60px;
      border-radius: var(--rad-sm, 4px);
      background: linear-gradient(
        90deg,
        var(--clr-border) 25%,
        var(--clr-surface-panel) 50%,
        var(--clr-border) 75%
      );
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
    }
    .shimmer-block.wide {
      width: 100px;
    }
    @keyframes shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }
  `,
})
export class TransactionSummaryFooterComponent {
  readonly settings = inject(AppSettingsService);
  summary = input.required<TransactionSummaryData>();
  loading = input<boolean>(false);
}
