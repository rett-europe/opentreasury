import {
  ChangeDetectionStrategy, Component, effect, inject, input, output, signal,
} from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { AppSettingsService } from '@core/services/app-settings.service';
import { TransactionService } from '@core/services/transaction.service';
import { StatusBadgeComponent } from '@shared/components/status-badge/status-badge.component';
import { ReviewStatus, Transaction } from '@shared/models/transaction.model';

@Component({
  selector: 'app-transaction-review',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatFormFieldModule, MatSelectModule, StatusBadgeComponent],
  template: `
    <div class="review-section">
      <h3>{{ settings.labels().reviewStatus }}</h3>
      <div class="review-row">
        <app-status-badge [status]="status()" />

        @if (isAdmin()) {
          <mat-form-field appearance="outline" class="review-select">
            <mat-label>{{ settings.labels().changeStatus }}</mat-label>
            <mat-select [value]="status()"
                        (selectionChange)="onStatusChange($event.value)"
                        [disabled]="saving()">
              <mat-option value="pending">{{ settings.labels().statusPending }}</mat-option>
              <mat-option value="reviewed">{{ settings.labels().statusReviewed }}</mat-option>
              <mat-option value="approved">{{ settings.labels().statusApproved }}</mat-option>
              <mat-option value="flagged">{{ settings.labels().statusFlagged }}</mat-option>
            </mat-select>
          </mat-form-field>
        }
      </div>
      @if (reviewedByName()) {
        <div class="last-reviewed">
          {{ settings.labels().lastReviewedBy }}
          {{ reviewedByName() }} &middot; {{ formatDate(reviewedAt()!) }}
        </div>
      }
    </div>
  `,
  styles: `
    .review-section {
      margin: var(--spc-24) 0 var(--spc-16);
      padding: var(--spc-16);
      background: var(--clr-surface-panel);
      border-radius: var(--rad-md);
    }
    .review-section h3 {
      font-size: var(--font-md);
      font-weight: var(--fw-medium);
      color: var(--clr-text-primary);
      margin: 0 0 var(--spc-12);
    }
    .review-row {
      display: flex;
      align-items: center;
      gap: var(--spc-12);
    }
    .review-select { width: 160px; }
    .last-reviewed {
      font-size: var(--font-sm);
      color: var(--clr-text-muted);
      margin-top: var(--spc-4);
    }
  `,
})
export class TransactionReviewComponent {
  transactionId = input.required<string>();
  year = input.required<number>();
  month = input.required<number>();
  currentStatus = input.required<string>();
  reviewedByName = input<string | null>(null);
  reviewedAt = input<string | null>(null);
  isAdmin = input(false);

  statusChanged = output<Transaction>();

  readonly status = signal<ReviewStatus>('pending');
  readonly saving = signal(false);

  readonly settings = inject(AppSettingsService);
  private readonly transactionService = inject(TransactionService);

  constructor() {
    effect(() => this.status.set(this.currentStatus() as ReviewStatus));
  }

  onStatusChange(newStatus: string): void {
    if (this.saving()) return;
    this.saving.set(true);
    this.transactionService
      .review(this.transactionId(), { reviewStatus: newStatus as ReviewStatus }, this.year(), this.month())
      .subscribe({
        next: (tx) => {
          this.status.set(tx.reviewStatus as ReviewStatus);
          this.saving.set(false);
          this.statusChanged.emit(tx);
        },
        error: () => this.saving.set(false),
      });
  }

  formatDate(iso: string): string {
    const d = new Date(iso);
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
  }
}
