import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AppSettingsService } from '@core/services/app-settings.service';
import { BULK_CATEGORIZE_MAX } from '@shared/models/transaction.model';

/**
 * Sticky bulk-action bar shown above the transactions table when at least one
 * row is selected. Dumb presenter — all selection state and actions live in the
 * parent (`TransactionListComponent`). See spec §6 / A-7 / A-8.
 */
@Component({
  selector: 'app-bulk-action-bar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CurrencyPipe, MatButtonModule, MatIconModule, MatTooltipModule],
  template: `
    <section class="bulk-bar" role="region" [attr.aria-label]="settings.labels().bulkChangeCategory">
      <div class="bulk-bar-summary">
        <mat-icon class="bulk-bar-check">check_circle</mat-icon>
        <span class="bulk-bar-count">{{ settings.labels().bulkSelectedCount(selectedCount) }}</span>
        <span class="bulk-bar-sep">·</span>
        <span class="bulk-bar-net">
          {{ settings.labels().bulkNetLabel }}:
          <span [class.income-amount]="net > 0" [class.expense-amount]="net < 0">
            {{ net | currency: 'EUR':'symbol':'1.2-2' }}
          </span>
        </span>
      </div>

      <div class="bulk-bar-actions">
        <button
          mat-flat-button
          color="primary"
          [disabled]="overLimit"
          [matTooltip]="overLimit ? settings.labels().bulkBatchLimit(maxBatch) : ''"
          (click)="changeCategory.emit()"
        >
          <mat-icon>label</mat-icon>
          {{ settings.labels().bulkChangeCategory }}
        </button>
        <button mat-stroked-button (click)="clearSelection.emit()">
          {{ settings.labels().bulkClearSelection }}
        </button>
      </div>
    </section>
  `,
  styles: `
    :host {
      display: block;
    }
    .bulk-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--spc-16);
      padding: var(--spc-8) var(--spc-16);
      background: var(--clr-surface-variant, #f5f5f5);
      border-bottom: 1px solid var(--clr-border, #e0e0e0);
      flex-wrap: wrap;
    }
    .bulk-bar-summary {
      display: flex;
      align-items: center;
      gap: var(--spc-8);
      font-size: var(--font-sm, 14px);
      font-weight: 500;
    }
    .bulk-bar-check {
      color: var(--mat-sys-primary, #1976d2);
    }
    .bulk-bar-sep {
      color: var(--clr-text-muted, #78717c);
    }
    .bulk-bar-net {
      color: var(--clr-text-muted, #78717c);
      font-weight: 400;
    }
    .bulk-bar-actions {
      display: flex;
      gap: var(--spc-8);
    }
    .income-amount { color: #4caf50; font-weight: 500; }
    .expense-amount { color: #e53935; font-weight: 500; }
  `,
})
export class BulkActionBarComponent {
  readonly settings = inject(AppSettingsService);

  @Input({ required: true }) selectedCount = 0;
  @Input({ required: true }) net = 0;
  @Input() maxBatch = BULK_CATEGORIZE_MAX;

  @Output() readonly changeCategory = new EventEmitter<void>();
  @Output() readonly clearSelection = new EventEmitter<void>();

  get overLimit(): boolean {
    return this.selectedCount > this.maxBatch;
  }
}
