import { Component, inject, computed, signal, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSettingsService } from '@core/services/app-settings.service';
import { TransactionService } from '@core/services/transaction.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { Transaction, TransactionType } from '@shared/models/transaction.model';
import { Category, Subcategory } from '@shared/models/category.model';

export interface QuickCategorizeData {
  transaction: Transaction;
}

@Component({
  selector: 'app-quick-categorize-dialog',
  standalone: true,
  imports: [
    MatDialogModule,
    MatFormFieldModule,
    MatSelectModule,
    MatButtonModule,
    MatSnackBarModule,
    CurrencyPipe,
    DatePipe,
    FormsModule,
  ],
  template: `
    <h2 mat-dialog-title>{{ settings.labels().categorizeTitle }}</h2>
    <mat-dialog-content>
      <div class="tx-summary">
        <span class="tx-type" [style.color]="typeColor()">{{ typeLabel() }}</span>
        <span class="tx-amount"
              [class.income-amount]="data.transaction.amount > 0"
              [class.expense-amount]="data.transaction.amount < 0">
          {{ data.transaction.amount | currency: 'EUR':'symbol':'1.2-2' }}
        </span>
        <span class="tx-date">{{ data.transaction.date | date: 'dd/MM/yyyy' }}</span>
      </div>

      <mat-form-field appearance="outline" class="full-width">
        <mat-label>{{ settings.labels().category }}</mat-label>
        <mat-select [(ngModel)]="selectedCategoryId" (selectionChange)="onCategoryChange()">
          <mat-option [value]="null">{{ settings.labels().clearCategory }}</mat-option>
          @for (cat of filteredCategories(); track cat.id) {
            <mat-option [value]="cat.id">{{ cat.name }}</mat-option>
          }
        </mat-select>
      </mat-form-field>

      @if (subcategories().length > 0) {
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>{{ settings.labels().subcategory }}</mat-label>
          <mat-select [(ngModel)]="selectedSubcategoryId">
            <mat-option [value]="null">—</mat-option>
            @for (sub of subcategories(); track sub.id) {
              <mat-option [value]="sub.id">{{ sub.name }}</mat-option>
            }
          </mat-select>
        </mat-form-field>
      }
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>{{ settings.labels().cancel }}</button>
      <button mat-flat-button color="primary"
              (click)="onCategorize()"
              [disabled]="saving()">
        {{ settings.labels().categorizeButton }}
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    .tx-summary {
      display: flex;
      gap: 12px;
      align-items: center;
      padding: 8px 12px;
      background: #f5f5f5;
      border-radius: 8px;
      margin-bottom: 16px;
      font-size: 14px;
    }
    .tx-type { font-weight: 500; }
    .tx-date { color: #78717c; }
    .income-amount { color: #4caf50; font-weight: 500; }
    .expense-amount { color: #e53935; font-weight: 500; }
    .full-width { width: 100%; }
  `,
})
export class QuickCategorizeDialogComponent implements OnInit {
  readonly data = inject<QuickCategorizeData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<QuickCategorizeDialogComponent>);
  private readonly transactionService = inject(TransactionService);
  private readonly refData = inject(ReferenceDataService);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);

  readonly saving = signal(false);

  selectedCategoryId: string | null = null;
  selectedSubcategoryId: string | null = null;

  readonly filteredCategories = computed((): Category[] => {
    const txType: TransactionType = this.data.transaction.transactionType;
    const cats = this.refData.categories().filter(c => c.isActive);
    if (txType === 'income') return cats.filter(c => c.categoryType === 'income');
    if (txType === 'expense') return cats.filter(c => c.categoryType === 'expense');
    return cats; // transfer/refund show all
  });

  readonly subcategories = computed((): Subcategory[] => {
    if (!this.selectedCategoryId) return [];
    const cat = this.refData.categories().find(c => c.id === this.selectedCategoryId);
    return cat?.subcategories.filter(s => s.isActive) ?? [];
  });

  readonly typeColor = computed(() => {
    switch (this.data.transaction.transactionType) {
      case 'income': return '#4caf50';
      case 'expense': return '#e53935';
      case 'transfer': return '#1e88e5';
      case 'refund': return '#00897b';
      default: return '#78717c';
    }
  });

  readonly typeLabel = computed(() => {
    const labels = this.settings.labels();
    switch (this.data.transaction.transactionType) {
      case 'income': return labels.incomeOption;
      case 'expense': return labels.expenseOption;
      case 'transfer': return labels.transferType;
      case 'refund': return labels.refundType;
      default: return '';
    }
  });

  ngOnInit(): void {
    this.selectedCategoryId = this.data.transaction.categoryId;
    this.selectedSubcategoryId = this.data.transaction.subcategoryId ?? null;
  }

  onCategoryChange(): void {
    this.selectedSubcategoryId = null;
  }

  onCategorize(): void {
    this.saving.set(true);
    const tx = this.data.transaction;
    this.transactionService
      .categorize(
        tx.id,
        { categoryId: this.selectedCategoryId, subcategoryId: this.selectedSubcategoryId },
        tx.year,
        tx.month,
      )
      .subscribe({
        next: (updated) => {
          this.snackBar.open(this.settings.labels().categorizationSaved, this.settings.labels().close, { duration: 3000 });
          this.dialogRef.close(updated);
        },
        error: () => {
          this.saving.set(false);
        },
      });
  }
}
