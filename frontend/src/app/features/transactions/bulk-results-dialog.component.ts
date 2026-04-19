import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AppSettingsService } from '@core/services/app-settings.service';
import { BulkCategorizeFailure } from '@shared/models/transaction.model';

export interface BulkResultsDialogData {
  succeeded: string[];
  failed: BulkCategorizeFailure[];
}

/**
 * Opened from the partial-failure snackbar (§8.3). Plain list of failed
 * transaction IDs with their error reason — no inline retry (users just re-pick
 * the remaining selected rows and Apply again, per AC-25).
 */
@Component({
  selector: 'app-bulk-results-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <h2 mat-dialog-title>{{ settings.labels().bulkPartialResultsTitle }}</h2>
    <mat-dialog-content class="results">
      <p class="summary">
        {{ settings.labels().bulkPartialFailureToast(data.succeeded.length, data.failed.length) }}
      </p>
      <ul class="failures">
        @for (f of data.failed; track f.id) {
          <li>
            <mat-icon class="fail-icon" aria-hidden="true">error_outline</mat-icon>
            <code class="fail-id">{{ f.id }}</code>
            <span class="fail-reason">{{ reason(f) }}</span>
          </li>
        }
      </ul>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-flat-button color="primary" mat-dialog-close>
        {{ settings.labels().close }}
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    .results { min-width: 360px; max-width: 520px; }
    .summary { margin: 0 0 12px; }
    .failures { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; max-height: 320px; overflow-y: auto; }
    .failures li { display: grid; grid-template-columns: 18px auto 1fr; gap: 8px; align-items: start; padding: 6px 8px; background: #fff3f3; border-radius: 6px; font-size: 13px; }
    .fail-icon { color: #c62828; font-size: 18px; width: 18px; height: 18px; }
    .fail-id { font-family: monospace; color: #333; }
    .fail-reason { color: #8b1a2b; }
  `,
})
export class BulkResultsDialogComponent {
  readonly data = inject<BulkResultsDialogData>(MAT_DIALOG_DATA);
  readonly settings = inject(AppSettingsService);

  reason(f: BulkCategorizeFailure): string {
    const labels = this.settings.labels();
    switch (f.code) {
      case 'NOT_FOUND':
        return labels.bulkFailureCodeNotFound;
      case 'SPLIT_PARENT_NOT_BULK_UPDATABLE':
        return labels.bulkFailureCodeSplitParent;
      case 'INVALID_SUBCATEGORY':
        return labels.bulkFailureCodeInvalidSubcategory;
      case 'INACTIVE_CATEGORY':
        return labels.bulkFailureCodeInactiveCategory;
      case 'CONCURRENCY_CONFLICT':
        return labels.bulkFailureCodeConcurrency;
      default:
        // Unknown code: surface the server-provided message if any, else fall back.
        return f.message?.trim() || labels.bulkFailureCodeUnknown;
    }
  }
}
