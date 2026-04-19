import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Output,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule, CurrencyPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatRadioModule } from '@angular/material/radio';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';

import { AppSettingsService } from '@core/services/app-settings.service';
import { TransactionService } from '@core/services/transaction.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { Category, Subcategory } from '@shared/models/category.model';
import {
  BULK_CATEGORIZE_MAX,
  BulkCategorizeAction,
  BulkCategorizeResponse,
  Transaction,
} from '@shared/models/transaction.model';

export interface BulkCategorizeDialogData {
  /**
   * Snapshot of the transactions the admin had selected at the moment the dialog opened.
   * Filter changes in the list underneath the dialog do NOT mutate this snapshot
   * (see spec EC-7 / EC-13).
   */
  transactions: Transaction[];
  /** Chosen category defaults to the most-common category in the selection, if any. */
  initialCategoryId?: string | null;
  initialSubcategoryId?: string | null;
}

export interface BulkCategorizeDialogResult {
  response: BulkCategorizeResponse;
  /** Action the user applied — used by the caller to re-fetch / refresh rows. */
  action: BulkCategorizeAction;
  /** Chosen category/subcategory when `action === 'apply'`, else null. */
  categoryId: string | null;
  subcategoryId: string | null;
}

@Component({
  selector: 'app-bulk-categorize-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    CurrencyPipe,
    FormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatSelectModule,
    MatRadioModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDividerModule,
  ],
  template: `
    <h2 mat-dialog-title>{{ settings.labels().bulkDialogTitle(data.transactions.length) }}</h2>

    <mat-dialog-content class="bulk-content">
      @if (serverError()) {
        <div class="bulk-banner bulk-banner-error" role="alert">
          <mat-icon>error_outline</mat-icon>
          <span>{{ settings.labels().bulkFailureBanner }}</span>
        </div>
      }

      <section class="bulk-summary" aria-live="polite">
        <div>{{ settings.labels().bulkSelectionSummary(data.transactions.length) }}</div>
        <div class="bulk-summary-net">
          {{ settings.labels().bulkNetLabel }}:
          <span [class.income-amount]="net() > 0" [class.expense-amount]="net() < 0">
            {{ net() | currency: 'EUR':'symbol':'1.2-2' }}
          </span>
        </div>
        <div class="bulk-summary-breakdown">
          {{
            settings.labels().bulkSelectionBreakdown(
              uncategorizedCount(),
              willBeOverwrittenCount()
            )
          }}
        </div>
      </section>

      @if (splitParentCount() > 0) {
        <div class="bulk-banner bulk-banner-warn" role="status">
          <mat-icon>warning_amber</mat-icon>
          <span>{{ settings.labels().bulkSplitParentWarning(splitParentCount()) }}</span>
          <button
            mat-button
            class="bulk-banner-action"
            (click)="onDeselectSplitParents()"
            [disabled]="saving()"
          >
            {{ settings.labels().bulkSplitParentDeselect }}
          </button>
        </div>
      }

      @if (transferCount() > 0) {
        <div class="bulk-banner bulk-banner-info" role="status">
          <mat-icon>info_outline</mat-icon>
          <span>{{ settings.labels().bulkTransferInfo(transferCount()) }}</span>
        </div>
      }

      <mat-radio-group [(ngModel)]="mode" class="bulk-mode-group" [disabled]="saving()">
        <mat-radio-button value="apply">
          {{ settings.labels().bulkModeApply(effectiveCount()) }}
        </mat-radio-button>
        <mat-radio-button value="clear">
          {{ settings.labels().bulkModeClear(effectiveCount()) }}
        </mat-radio-button>
      </mat-radio-group>

      @if (mode === 'apply') {
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>{{ settings.labels().category }}</mat-label>
          <mat-select
            [(ngModel)]="selectedCategoryId"
            (selectionChange)="onCategoryChange()"
            [disabled]="saving()"
          >
            @for (cat of activeCategories(); track cat.id) {
              <mat-option [value]="cat.id">{{ cat.name }}</mat-option>
            }
          </mat-select>
        </mat-form-field>

        @if (activeSubcategories().length > 0) {
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>{{ settings.labels().subcategory }}</mat-label>
            <mat-select [(ngModel)]="selectedSubcategoryId" [disabled]="saving()">
              <mat-option [value]="null">{{ settings.labels().bulkSubcategoryNone }}</mat-option>
              @for (sub of activeSubcategories(); track sub.id) {
                <mat-option [value]="sub.id">{{ sub.name }}</mat-option>
              }
            </mat-select>
          </mat-form-field>
        }
      }
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button [disabled]="saving()" (click)="onCancel()">
        {{ settings.labels().cancel }}
      </button>
      <button
        mat-flat-button
        color="primary"
        [disabled]="!canApply()"
        (click)="onApply()"
      >
        @if (saving()) {
          <mat-spinner diameter="18" class="inline-spinner" />
        }
        {{ settings.labels().bulkApplyButton }}
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    .bulk-content { display: flex; flex-direction: column; gap: 12px; min-width: 380px; }
    .bulk-summary { padding: 8px 12px; background: #f5f5f5; border-radius: 8px; font-size: 14px; display: flex; flex-direction: column; gap: 4px; }
    .bulk-summary-net, .bulk-summary-breakdown { color: #78717c; font-size: 13px; }
    .bulk-banner { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; font-size: 13px; }
    .bulk-banner mat-icon { flex-shrink: 0; }
    .bulk-banner-warn { background: #fff3cd; color: #8a6d3b; }
    .bulk-banner-info { background: #e8f4fd; color: #31708f; }
    .bulk-banner-error { background: #f8d7da; color: #8b1a2b; }
    .bulk-banner-action { margin-left: auto; }
    .bulk-mode-group { display: flex; flex-direction: column; gap: 4px; margin-top: 4px; }
    .full-width { width: 100%; }
    .income-amount { color: #4caf50; font-weight: 500; }
    .expense-amount { color: #e53935; font-weight: 500; }
    .inline-spinner { display: inline-block; margin-right: 6px; vertical-align: middle; }
  `,
})
export class BulkCategorizeDialogComponent {
  readonly data = inject<BulkCategorizeDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<BulkCategorizeDialogComponent, BulkCategorizeDialogResult>);
  private readonly transactionService = inject(TransactionService);
  private readonly refData = inject(ReferenceDataService);
  readonly settings = inject(AppSettingsService);

  /** Mutable snapshot — the Deselect split-parents button may prune it. */
  private readonly workingSelection = signal<Transaction[]>(this.data.transactions.slice());

  readonly saving = signal(false);
  readonly serverError = signal(false);

  // ngModel-bound state — exposed directly (non-signal) for simpler two-way binding.
  mode: BulkCategorizeAction = 'apply';
  selectedCategoryId: string | null = this.data.initialCategoryId ?? null;
  selectedSubcategoryId: string | null = this.data.initialSubcategoryId ?? null;

  /** Signal exposed to the caller so parent can detect deselect-parent edits. */
  @Output() readonly deselected = new EventEmitter<string[]>();

  readonly activeCategories = computed<Category[]>(() =>
    this.refData.categories().filter((c) => c.isActive),
  );

  readonly activeSubcategories = computed<Subcategory[]>(() => {
    if (!this.selectedCategoryId) return [];
    const cat = this.refData.categories().find((c) => c.id === this.selectedCategoryId);
    return cat?.subcategories.filter((s) => s.isActive) ?? [];
  });

  readonly splitParentCount = computed(
    () => this.workingSelection().filter((t) => t.isSplit).length,
  );

  readonly transferCount = computed(
    () => this.workingSelection().filter((t) => t.transactionType === 'transfer').length,
  );

  /** Effective targets = selection minus split parents (backend will reject parents anyway). */
  readonly effectiveSelection = computed(() =>
    this.workingSelection().filter((t) => !t.isSplit),
  );
  readonly effectiveCount = computed(() => this.effectiveSelection().length);

  readonly net = computed(() =>
    this.workingSelection().reduce((acc, t) => acc + Number(t.amount || 0), 0),
  );

  readonly uncategorizedCount = computed(
    () => this.workingSelection().filter((t) => !t.categoryId).length,
  );

  readonly willBeOverwrittenCount = computed(
    () => this.workingSelection().length - this.uncategorizedCount(),
  );

  readonly canApply = computed(() => {
    if (this.saving()) return false;
    if (this.effectiveCount() === 0) return false;
    if (this.effectiveCount() > BULK_CATEGORIZE_MAX) return false;
    if (this.mode === 'apply') return !!this.selectedCategoryId;
    return true; // clear mode
  });

  onCategoryChange(): void {
    this.selectedSubcategoryId = null;
  }

  onDeselectSplitParents(): void {
    const kept = this.workingSelection().filter((t) => !t.isSplit);
    const removed = this.workingSelection()
      .filter((t) => t.isSplit)
      .map((t) => t.id);
    if (removed.length === 0) return;
    this.workingSelection.set(kept);
    this.deselected.emit(removed);
  }

  onCancel(): void {
    if (this.saving()) return;
    this.dialogRef.close();
  }

  onApply(): void {
    if (!this.canApply()) return;
    this.saving.set(true);
    this.serverError.set(false);

    const effective = this.effectiveSelection();
    const action = this.mode;
    const categoryId = action === 'apply' ? this.selectedCategoryId : null;
    const subcategoryId = action === 'apply' ? this.selectedSubcategoryId : null;

    this.transactionService
      .bulkCategorize({
        items: effective.map((t) => ({ id: t.id, year: t.year, month: t.month })),
        action,
        categoryId,
        subcategoryId,
      })
      .subscribe({
        next: (response) => {
          this.dialogRef.close({ response, action, categoryId, subcategoryId });
        },
        error: () => {
          // Total failure (§8.4): keep dialog open, show banner, let the admin retry.
          this.serverError.set(true);
          this.saving.set(false);
        },
      });
  }
}
