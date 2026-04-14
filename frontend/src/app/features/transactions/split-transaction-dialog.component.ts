import { Component, inject, computed, signal, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { CurrencyPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSettingsService } from '@core/services/app-settings.service';
import { TransactionService } from '@core/services/transaction.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { Transaction } from '@shared/models/transaction.model';
import { Category, Subcategory } from '@shared/models/category.model';

export interface SplitTransactionDialogData {
  transaction: Transaction;
}

interface SplitLineForm {
  amount: number | null;
  categoryId: string | null;
  subcategoryId: string | null;
  tagIds: string[];
  detail: string;
}

@Component({
  selector: 'app-split-transaction-dialog',
  standalone: true,
  imports: [
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatDividerModule,
    MatSnackBarModule,
    MatTooltipModule,
    CurrencyPipe,
    FormsModule,
  ],
  template: `
    <h2 mat-dialog-title>{{ settings.labels().splitTitle }}</h2>

    <mat-dialog-content>
      <p class="subtitle">{{ settings.labels().splitDialogSubtitle }}</p>

      <!-- Original amount summary -->
      <div class="amount-summary">
        <div class="summary-row">
          <span class="summary-label">{{ settings.labels().splitOriginalAmount }}</span>
          <span class="summary-value original">
            {{ Math.abs(data.transaction.amount) | currency: 'EUR':'symbol':'1.2-2' }}
          </span>
        </div>
        <div class="summary-row">
          <span class="summary-label">{{ settings.labels().splitRemaining }}</span>
          <span class="summary-value" [class.remaining-ok]="remaining() === 0" [class.remaining-error]="remaining() !== 0">
            {{ remaining() | currency: 'EUR':'symbol':'1.2-2' }}
          </span>
        </div>
      </div>

      <mat-divider class="divider" />

      <!-- Split lines -->
      <div class="split-lines-header">
        <span class="split-lines-title">{{ settings.labels().splitLinesTitle }}</span>
      </div>

      @for (line of splitLines(); track $index) {
        <div class="split-line">
          <div class="line-number">{{ $index + 1 }}</div>

          <div class="line-fields">
            <div class="line-row-main">
              <!-- Amount -->
              <mat-form-field appearance="outline" class="field-amount">
                <mat-label>{{ settings.labels().splitLineAmount }}</mat-label>
                <input matInput type="number" min="0.01" step="0.01"
                       [(ngModel)]="line.amount"
                       (ngModelChange)="onAmountChange()" />
              </mat-form-field>

              <!-- Category -->
              <mat-form-field appearance="outline" class="field-category">
                <mat-label>{{ settings.labels().categoryOptional }}</mat-label>
                <mat-select [(ngModel)]="line.categoryId"
                            (ngModelChange)="onLineCategoryChange($index)">
                  <mat-option [value]="null">{{ settings.labels().clearCategory }}</mat-option>
                  @for (cat of filteredCategories(); track cat.id) {
                    <mat-option [value]="cat.id">{{ cat.name }}</mat-option>
                  }
                </mat-select>
              </mat-form-field>

              <!-- Subcategory -->
              <mat-form-field appearance="outline" class="field-subcategory">
                <mat-label>{{ settings.labels().subcategoryOptional }}</mat-label>
                <mat-select [(ngModel)]="line.subcategoryId"
                            [disabled]="!line.categoryId">
                  <mat-option [value]="null">—</mat-option>
                  @for (sub of getSubcategories($index); track sub.id) {
                    <mat-option [value]="sub.id">{{ sub.name }}</mat-option>
                  }
                </mat-select>
              </mat-form-field>
            </div>

            <!-- Detail -->
            <mat-form-field appearance="outline" class="field-detail">
              <mat-label>{{ settings.labels().splitLineDetail }}</mat-label>
              <input matInput [(ngModel)]="line.detail" maxlength="500" />
            </mat-form-field>
          </div>

          <!-- Remove button -->
          <button mat-icon-button color="warn" class="remove-btn"
                  [disabled]="splitLines().length <= 2"
                  [matTooltip]="settings.labels().splitRemoveLine"
                  (click)="removeLine($index)">
            <mat-icon>remove_circle_outline</mat-icon>
          </button>
        </div>

        @if ($index < splitLines().length - 1) {
          <mat-divider class="line-divider" />
        }
      }

      <!-- Add line -->
      <button mat-stroked-button class="add-line-btn" (click)="addLine()">
        <mat-icon>add</mat-icon>
        {{ settings.labels().splitAddLine }}
      </button>

      <!-- Validation error -->
      @if (validationError()) {
        <div class="validation-error">{{ validationError() }}</div>
      }
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>{{ settings.labels().cancel }}</button>
      <button mat-flat-button color="primary"
              [disabled]="saving() || !isValid()"
              (click)="onSave()">
        {{ saving() ? settings.labels().saving : settings.labels().splitSave }}
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    .subtitle {
      color: var(--clr-text-muted, #78717c);
      font-size: var(--font-sm, 13px);
      margin-bottom: 16px;
    }
    .amount-summary {
      background: var(--clr-surface-variant, #f5f5f5);
      border-radius: var(--rad-md, 8px);
      padding: 12px 16px;
      margin-bottom: 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .summary-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: var(--font-sm, 13px);
    }
    .summary-label { color: var(--clr-text-muted, #78717c); }
    .summary-value { font-weight: 600; font-size: var(--font-md, 15px); }
    .summary-value.original { color: var(--clr-text, #1c1b1f); }
    .remaining-ok { color: #4caf50; }
    .remaining-error { color: #e53935; }
    .divider { margin: 16px 0; }
    .line-divider { margin: 8px 0; }
    .split-lines-header {
      margin-bottom: 12px;
    }
    .split-lines-title {
      font-size: var(--font-sm, 13px);
      font-weight: 600;
      color: var(--clr-text-muted, #78717c);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .split-line {
      display: flex;
      gap: 8px;
      align-items: flex-start;
      padding: 8px 0;
    }
    .line-number {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--clr-primary, #6750a4);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 600;
      flex-shrink: 0;
      margin-top: 12px;
    }
    .line-fields {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0;
    }
    .line-row-main {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .field-amount { width: 120px; flex-shrink: 0; }
    .field-category { flex: 1; min-width: 150px; }
    .field-subcategory { flex: 1; min-width: 120px; }
    .field-detail { width: 100%; }
    .remove-btn { flex-shrink: 0; margin-top: 4px; }
    .add-line-btn {
      width: 100%;
      margin-top: 8px;
    }
    .validation-error {
      color: #e53935;
      font-size: var(--font-sm, 13px);
      margin-top: 8px;
      padding: 8px 12px;
      background: #ffebee;
      border-radius: 4px;
    }
  `,
})
export class SplitTransactionDialogComponent implements OnInit {
  protected readonly Math = Math;

  readonly data = inject<SplitTransactionDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<SplitTransactionDialogComponent>);
  private readonly transactionService = inject(TransactionService);
  private readonly refData = inject(ReferenceDataService);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);

  readonly saving = signal(false);
  readonly splitLines = signal<SplitLineForm[]>([]);
  readonly validationError = signal<string | null>(null);

  readonly filteredCategories = computed((): Category[] => {
    const txType = this.data.transaction.transactionType;
    const cats = this.refData.categories().filter(c => c.isActive);
    if (txType === 'income') return cats.filter(c => c.categoryType === 'income');
    if (txType === 'expense') return cats.filter(c => c.categoryType === 'expense');
    return cats;
  });

  readonly totalAssigned = computed((): number => {
    return this.splitLines().reduce((sum, l) => sum + (l.amount ?? 0), 0);
  });

  readonly remaining = computed((): number => {
    const abs = Math.abs(this.data.transaction.amount);
    return Math.round((abs - this.totalAssigned()) * 100) / 100;
  });

  readonly isValid = computed((): boolean => {
    const lines = this.splitLines();
    if (lines.length < 2) return false;
    if (lines.some(l => !l.amount || l.amount <= 0)) return false;
    return this.remaining() === 0;
  });

  ngOnInit(): void {
    const tx = this.data.transaction;
    if (tx.isSplit && tx.splits?.length >= 2) {
      // Pre-populate from existing splits
      this.splitLines.set(
        tx.splits.map(s => ({
          amount: s.amount,
          categoryId: s.categoryId,
          subcategoryId: s.subcategoryId,
          tagIds: s.tagIds ?? [],
          detail: s.detail ?? '',
        }))
      );
    } else {
      // Start with 2 empty lines
      this.splitLines.set([this.emptyLine(), this.emptyLine()]);
    }
  }

  private emptyLine(): SplitLineForm {
    return { amount: null, categoryId: null, subcategoryId: null, tagIds: [], detail: '' };
  }

  getSubcategories(lineIndex: number): Subcategory[] {
    const catId = this.splitLines()[lineIndex]?.categoryId;
    if (!catId) return [];
    const cat = this.refData.categories().find(c => c.id === catId);
    return cat?.subcategories.filter(s => s.isActive) ?? [];
  }

  onAmountChange(): void {
    this.validationError.set(null);
  }

  onLineCategoryChange(lineIndex: number): void {
    const lines = [...this.splitLines()];
    lines[lineIndex] = { ...lines[lineIndex], subcategoryId: null };
    this.splitLines.set(lines);
  }

  addLine(): void {
    this.splitLines.set([...this.splitLines(), this.emptyLine()]);
  }

  removeLine(index: number): void {
    if (this.splitLines().length <= 2) return;
    const lines = [...this.splitLines()];
    lines.splice(index, 1);
    this.splitLines.set(lines);
  }

  onSave(): void {
    if (!this.isValid()) {
      const labels = this.settings.labels();
      if (this.splitLines().length < 2) {
        this.validationError.set(labels.splitMinLines);
      } else {
        this.validationError.set(labels.splitAmountMismatch);
      }
      return;
    }

    const tx = this.data.transaction;
    const splits = this.splitLines().map(l => ({
      amount: l.amount!,
      categoryId: l.categoryId,
      subcategoryId: l.subcategoryId,
      tagIds: l.tagIds,
      detail: l.detail || null,
    }));

    this.saving.set(true);
    this.transactionService
      .split(tx.id, { splits }, tx.year, tx.month)
      .subscribe({
        next: (updated) => {
          this.snackBar.open(this.settings.labels().splitSaved, this.settings.labels().close, { duration: 3000 });
          this.dialogRef.close(updated);
        },
        error: () => {
          this.saving.set(false);
          this.validationError.set(this.settings.labels().splitValidationError);
        },
      });
  }
}
