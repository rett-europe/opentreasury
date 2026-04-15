import {
  ChangeDetectionStrategy, Component, computed, inject, OnInit, signal,
} from '@angular/core';
import {
  FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators,
} from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { AppSettingsService } from '@core/services/app-settings.service';
import { TransactionService } from '@core/services/transaction.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { Transaction, SplitRequest } from '@shared/models/transaction.model';
import { Category, Subcategory } from '@shared/models/category.model';
import { Tag } from '@shared/models/tag.model';

export interface SplitDialogData {
  transaction: Transaction;
}

const MAX_LINES = 20;
const MIN_LINES = 2;

@Component({
  selector: 'app-split-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatSnackBarModule,
    MatProgressBarModule,
    CurrencyPipe,
    DatePipe,
  ],
  template: `
    <h2 mat-dialog-title>{{ settings.labels().splitDialogTitle }}</h2>

    <mat-dialog-content class="split-content">
      <!-- Parent summary -->
      <div class="parent-summary" [class]="'type-' + data.transaction.transactionType">
        <span class="parent-date">{{ data.transaction.date | date: 'dd/MM/yyyy' }}</span>
        <span class="parent-desc">{{ data.transaction.bankDescription || data.transaction.detail || '—' }}</span>
        <span class="parent-amount">
          {{ data.transaction.amount | currency: 'EUR':'symbol':'1.2-2' }}
        </span>
      </div>

      <!-- Balance bar -->
      <div class="balance-bar">
        <div class="balance-labels">
          <span>{{ settings.labels().splitAllocated }}: {{ totalAllocated() | currency: 'EUR':'symbol':'1.2-2' }}</span>
          @if (remaining() > 0) {
            <span class="balance-warning">
              {{ settings.labels().splitUnallocated }}: {{ remaining() | currency: 'EUR':'symbol':'1.2-2' }}
            </span>
          } @else if (remaining() < 0) {
            <span class="balance-error">
              {{ settings.labels().splitOverAllocated(overAmount()) }}
            </span>
          } @else {
            <span class="balance-ok">{{ settings.labels().splitBalanced }}</span>
          }
        </div>
        <div class="progress-track">
          <div class="progress-fill"
               [class.progress-ok]="remaining() === 0"
               [class.progress-warning]="remaining() > 0"
               [class.progress-error]="remaining() < 0"
               [style.width.%]="allocationPercent()">
          </div>
        </div>
      </div>

      <!-- Split lines -->
      <div class="lines-container">
        @for (line of linesArray.controls; track $index; let i = $index) {
          <div class="split-line" [formGroup]="asFormGroup(line)">
            <span class="line-number">{{ i + 1 }}</span>

            <mat-form-field appearance="outline" class="field-amount">
              <mat-label>{{ settings.labels().amount }}</mat-label>
              <input matInput type="number" formControlName="amount"
                     step="0.01" min="0.01"
                     (input)="onAmountChange()">
              <span matTextPrefix>&euro;&nbsp;</span>
            </mat-form-field>

            <mat-form-field appearance="outline" class="field-category">
              <mat-label>{{ settings.labels().category }}</mat-label>
              <mat-select formControlName="categoryId"
                          (selectionChange)="onLineCategoryChange(i)">
                <mat-option [value]="null">—</mat-option>
                @for (cat of filteredCategories(); track cat.id) {
                  <mat-option [value]="cat.id">{{ cat.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline" class="field-subcategory">
              <mat-label>{{ settings.labels().subcategory }}</mat-label>
              <mat-select formControlName="subcategoryId">
                <mat-option [value]="null">—</mat-option>
                @for (sub of getSubcategories(i); track sub.id) {
                  <mat-option [value]="sub.id">{{ sub.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline" class="field-tags">
              <mat-label>{{ settings.labels().tags }}</mat-label>
              <mat-select formControlName="tagIds" multiple>
                @for (tag of activeTags(); track tag.id) {
                  <mat-option [value]="tag.id">{{ tag.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline" class="field-detail">
              <mat-label>{{ settings.labels().detail }}</mat-label>
              <input matInput formControlName="detail">
            </mat-form-field>

            <button mat-icon-button color="warn" type="button"
                    [disabled]="linesArray.length <= MIN_LINES"
                    (click)="removeLine(i)"
                    [matTooltip]="settings.labels().cancel">
              <mat-icon>close</mat-icon>
            </button>
          </div>
        }
      </div>

      <button mat-stroked-button type="button"
              [disabled]="linesArray.length >= MAX_LINES"
              (click)="addLine()"
              class="add-line-btn">
        <mat-icon>add</mat-icon>
        {{ settings.labels().addLine }}
      </button>

      @if (linesArray.length < MIN_LINES) {
        <p class="min-lines-hint">{{ settings.labels().splitMinLinesError }}</p>
      }
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      @if (isEdit) {
        <button mat-button color="warn" type="button"
                class="remove-split-btn"
                (click)="onRemoveSplit()">
          {{ settings.labels().removeSplit }}
        </button>
        <span class="spacer"></span>
      }
      <button mat-button type="button" (click)="onCancel()">
        {{ settings.labels().cancel }}
      </button>
      <button mat-flat-button color="primary" type="button"
              [disabled]="!canSave()"
              (click)="onSave()">
        {{ saving() ? settings.labels().saving : settings.labels().saveSplit }}
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    .split-content {
      min-width: 700px;
      max-height: 70vh;
      overflow-y: auto;
    }
    .parent-summary {
      display: flex;
      gap: var(--spc-12, 12px);
      align-items: center;
      padding: var(--spc-10, 10px) var(--spc-12, 12px);
      border-radius: var(--rad-md, 8px);
      margin-bottom: var(--spc-16, 16px);
      font-size: var(--font-sm, 14px);
    }
    .type-income { background: var(--clr-income-bg); }
    .type-expense { background: var(--clr-expense-bg); }
    .type-transfer { background: var(--clr-transfer-bg); }
    .type-refund { background: var(--clr-refund-bg); }
    .parent-desc {
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .parent-amount { font-weight: 600; }

    .balance-bar {
      margin-bottom: var(--spc-16, 16px);
    }
    .balance-labels {
      display: flex;
      justify-content: space-between;
      font-size: var(--font-xs, 12px);
      margin-bottom: var(--spc-4, 4px);
    }
    .balance-warning { color: var(--clr-warning); }
    .balance-error { color: var(--clr-error); }
    .balance-ok { color: var(--clr-success); font-weight: 600; }
    .progress-track {
      height: 6px;
      background: var(--clr-border);
      border-radius: var(--rad-pill, 100px);
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      border-radius: var(--rad-pill, 100px);
      transition: width 0.2s ease, background-color 0.2s ease;
    }
    .progress-ok { background: var(--clr-success); }
    .progress-warning { background: var(--clr-warning); }
    .progress-error { background: var(--clr-error); }

    .lines-container {
      display: flex;
      flex-direction: column;
      gap: var(--spc-8, 8px);
    }
    .split-line {
      display: flex;
      align-items: center;
      gap: var(--spc-8, 8px);
    }
    .line-number {
      width: 24px;
      text-align: center;
      font-size: var(--font-xs, 12px);
      color: var(--clr-text-muted);
      font-weight: 600;
      flex-shrink: 0;
    }
    .field-amount { width: 120px; flex-shrink: 0; }
    .field-category { width: 160px; flex-shrink: 0; }
    .field-subcategory { width: 140px; flex-shrink: 0; }
    .field-tags { width: 140px; flex-shrink: 0; }
    .field-detail { flex: 1; min-width: 120px; }
    .add-line-btn {
      margin-top: var(--spc-8, 8px);
    }
    .min-lines-hint {
      color: var(--clr-warning);
      font-size: var(--font-xs, 12px);
      margin-top: var(--spc-4, 4px);
    }

    mat-dialog-actions {
      display: flex;
    }
    .remove-split-btn {
      margin-right: auto;
    }
    .spacer { flex: 1; }

    /* Compact form fields inside dialog */
    :host ::ng-deep .mat-mdc-form-field-subscript-wrapper {
      display: none;
    }
  `,
})
export class SplitDialogComponent implements OnInit {
  readonly data = inject<SplitDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<SplitDialogComponent>);
  private readonly fb = inject(FormBuilder);
  private readonly transactionService = inject(TransactionService);
  private readonly refData = inject(ReferenceDataService);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);

  readonly saving = signal(false);
  readonly linesAmountSum = signal(0);
  readonly MIN_LINES = MIN_LINES;
  readonly MAX_LINES = MAX_LINES;

  linesArray!: FormArray;
  isEdit = false;

  private readonly parentAbsAmount = Math.abs(this.data.transaction.amount);

  // Derived signals
  readonly totalAllocated = computed(() => this.linesAmountSum());
  readonly remaining = computed(() =>
    Math.round((this.parentAbsAmount - this.linesAmountSum()) * 100) / 100,
  );
  readonly allocationPercent = computed(() => {
    if (this.parentAbsAmount === 0) return 0;
    return Math.min(100, (this.linesAmountSum() / this.parentAbsAmount) * 100);
  });
  readonly canSave = computed(() =>
    this.remaining() === 0
    && this.linesArray?.length >= MIN_LINES
    && !!this.linesArray?.valid
    && !this.saving(),
  );
  readonly overAmount = computed(() => {
    const abs = Math.abs(this.remaining());
    return abs.toFixed(2);
  });

  readonly filteredCategories = computed((): Category[] => {
    return this.refData.categories().filter(c => c.isActive);
  });

  readonly activeTags = computed((): Tag[] =>
    this.refData.tags().filter(t => t.isActive),
  );

  ngOnInit(): void {
    const tx = this.data.transaction;
    this.isEdit = tx.isSplit && tx.splitLines?.length > 0;
    this.linesArray = this.fb.array([]);

    if (this.isEdit) {
      // Load existing split lines
      for (const sl of tx.splitLines) {
        this.linesArray.push(this.createLineGroup(
          Math.abs(sl.amount),
          sl.categoryId,
          sl.subcategoryId,
          sl.tagIds ?? [],
          sl.detail,
        ));
      }
    } else if (tx.categoryId) {
      // Pre-populate: first line gets parent category + full amount
      this.linesArray.push(this.createLineGroup(
        this.parentAbsAmount,
        tx.categoryId,
        tx.subcategoryId ?? null,
        tx.tagIds ?? [],
        null,
      ));
      // Empty second line
      this.linesArray.push(this.createLineGroup(0, null, null, [], null));
    } else {
      // Two empty lines
      this.linesArray.push(this.createLineGroup(0, null, null, [], null));
      this.linesArray.push(this.createLineGroup(0, null, null, [], null));
    }

    this.recalcSum();
  }

  addLine(): void {
    if (this.linesArray.length >= MAX_LINES) return;
    const prefill = Math.max(0, Math.round(this.remaining() * 100) / 100);
    this.linesArray.push(this.createLineGroup(prefill, null, null, [], null));
    this.recalcSum();
  }

  removeLine(index: number): void {
    if (this.linesArray.length <= MIN_LINES) return;
    this.linesArray.removeAt(index);
    this.recalcSum();
  }

  onAmountChange(): void {
    this.recalcSum();
  }

  onLineCategoryChange(index: number): void {
    const group = this.linesArray.at(index) as FormGroup;
    group.get('subcategoryId')?.setValue(null);
  }

  getSubcategories(index: number): Subcategory[] {
    const group = this.linesArray.at(index) as FormGroup;
    const catId = group.get('categoryId')?.value;
    if (!catId) return [];
    const cat = this.refData.categories().find(c => c.id === catId);
    return cat?.subcategories.filter(s => s.isActive) ?? [];
  }

  asFormGroup(control: unknown): FormGroup {
    return control as FormGroup;
  }

  onSave(): void {
    if (!this.canSave()) return;
    this.saving.set(true);

    const tx = this.data.transaction;
    const request: SplitRequest = {
      lines: this.linesArray.controls.map((ctrl) => {
        const g = ctrl as FormGroup;
        return {
          amount: Math.abs(g.get('amount')?.value ?? 0),
          categoryId: g.get('categoryId')?.value || null,
          subcategoryId: g.get('subcategoryId')?.value || null,
          tagIds: g.get('tagIds')?.value ?? [],
          detail: g.get('detail')?.value || null,
        };
      }),
    };

    const op$ = this.isEdit
      ? this.transactionService.updateSplit(tx.id, request, tx.year, tx.month)
      : this.transactionService.createSplit(tx.id, request, tx.year, tx.month);

    op$.subscribe({
      next: (updated) => {
        this.snackBar.open(
          this.settings.labels().splitSaved,
          this.settings.labels().close,
          { duration: 3000 },
        );
        this.dialogRef.close(updated);
      },
      error: (err: { error?: { detail?: string } }) => {
        this.saving.set(false);
        const msg = err?.error?.detail || 'Failed to save split';
        this.snackBar.open(msg, this.settings.labels().close, { duration: 5000 });
      },
    });
  }

  onRemoveSplit(): void {
    const tx = this.data.transaction;
    const msg = this.settings.labels().splitRemoveConfirm(tx.splitCount);
    if (!confirm(msg)) return;
    this.saving.set(true);

    this.transactionService.unsplit(tx.id, tx.year, tx.month).subscribe({
      next: (updated) => {
        this.snackBar.open(
          this.settings.labels().splitRemoved,
          this.settings.labels().close,
          { duration: 3000 },
        );
        this.dialogRef.close(updated);
      },
      error: (err: { error?: { detail?: string } }) => {
        this.saving.set(false);
        const msg = err?.error?.detail || 'Failed to remove split';
        this.snackBar.open(msg, this.settings.labels().close, { duration: 5000 });
      },
    });
  }

  onCancel(): void {
    if (this.linesArray.dirty && !confirm(this.settings.labels().splitDiscardConfirm)) {
      return;
    }
    this.dialogRef.close(undefined);
  }

  private createLineGroup(
    amount: number,
    categoryId: string | null,
    subcategoryId: string | null,
    tagIds: string[],
    detail: string | null,
  ): FormGroup {
    return this.fb.group({
      amount: [amount, [Validators.required, Validators.min(0.01)]],
      categoryId: [categoryId],
      subcategoryId: [subcategoryId],
      tagIds: [tagIds],
      detail: [detail],
    });
  }

  private recalcSum(): void {
    let sum = 0;
    for (const ctrl of this.linesArray.controls) {
      const val = (ctrl as FormGroup).get('amount')?.value;
      sum += Number(val) || 0;
    }
    this.linesAmountSum.set(Math.round(sum * 100) / 100);
  }
}
