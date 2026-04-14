import {
  ChangeDetectionStrategy, Component, ElementRef, inject, OnInit,
  signal, computed, viewChild,
} from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatExpansionModule } from '@angular/material/expansion';
import { AppSettingsService } from '@core/services/app-settings.service';
import { AuthService } from '@core/auth/auth.service';
import { TransactionService } from '@core/services/transaction.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { Subcategory } from '@shared/models/category.model';
import {
  Transaction,
  TransactionCreate,
  TransactionType,
} from '@shared/models/transaction.model';
import { LoadingContainerComponent } from '@shared/components/loading-container/loading-container.component';
import { ErrorStateComponent } from '@shared/components/error-state/error-state.component';
import { PageHeaderComponent } from '@shared/components/page-header/page-header.component';
import { TypeIndicatorComponent } from './type-indicator.component';
import { TransactionNotesComponent } from './notes-section.component';
import { TransactionReviewComponent } from './review-status-section.component';

type TransactionTypeDisplay =
  | 'income' | 'expense'
  | 'transfer_in' | 'transfer_out'
  | 'refund_received' | 'refund_given';

const TYPE_MAP: Record<TransactionTypeDisplay, { transactionType: TransactionType; sign: 1 | -1 }> = {
  income:          { transactionType: 'income',   sign:  1 },
  expense:         { transactionType: 'expense',  sign: -1 },
  transfer_in:     { transactionType: 'transfer', sign:  1 },
  transfer_out:    { transactionType: 'transfer', sign: -1 },
  refund_received: { transactionType: 'refund',   sign:  1 },
  refund_given:    { transactionType: 'refund',   sign: -1 },
};

const LAST_ACCOUNT_KEY = 'opentreasury-last-account';

@Component({
  selector: 'app-transaction-form',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatSnackBarModule,
    MatExpansionModule,
    LoadingContainerComponent,
    ErrorStateComponent,
    PageHeaderComponent,
    TypeIndicatorComponent,
    TransactionNotesComponent,
    TransactionReviewComponent,
  ],
  host: {
    '(keydown.control.Enter)': 'onSaveAndNew()',
  },
  template: `
    <div class="page-container">
      <app-page-header [title]="isEdit ? settings.labels().editTransaction : settings.labels().newTransaction" />

      @if (loadError()) {
        <app-error-state
          message="Error loading transaction"
          retryLabel="Retry"
          (retry)="retryLoad()" />
      } @else {
        <app-loading-container [loading]="loadingForm()">
          <mat-card class="form-card">
            <mat-card-content>
              <form [formGroup]="form" (ngSubmit)="onSaveAndNew()">
                <!-- ROW 1: Type + Account + Currency badge -->
                <div class="form-row three-col">
                  <mat-form-field appearance="outline">
                    <mat-label>{{ settings.labels().transactionType }}</mat-label>
                    <mat-select formControlName="transactionTypeDisplay"
                                (selectionChange)="onTypeChange($event.value)">
                      @for (opt of typeOptions(); track opt.value) {
                        <mat-option [value]="opt.value">{{ opt.label }}</mat-option>
                      }
                    </mat-select>
                  </mat-form-field>

                  <mat-form-field appearance="outline">
                    <mat-label>{{ settings.labels().account }}</mat-label>
                    <mat-select formControlName="accountId">
                      @for (acc of activeAccounts(); track acc.id) {
                        <mat-option [value]="acc.id">{{ acc.accountLabel }}</mat-option>
                      }
                    </mat-select>
                  </mat-form-field>

                  <div class="currency-badge">EUR</div>
                </div>

                <!-- ROW 2: Dates -->
                <div class="form-row two-col">
                  <mat-form-field appearance="outline">
                    <mat-label>{{ settings.labels().date }}</mat-label>
                    <input matInput [matDatepicker]="picker" formControlName="date">
                    <mat-datepicker-toggle matIconSuffix [for]="picker" />
                    <mat-datepicker #picker />
                  </mat-form-field>

                  <mat-form-field appearance="outline">
                    <mat-label>{{ settings.labels().valueDate }}</mat-label>
                    <input matInput [matDatepicker]="valuePicker" formControlName="valueDate">
                    <mat-datepicker-toggle matIconSuffix [for]="valuePicker" />
                    <mat-datepicker #valuePicker />
                  </mat-form-field>
                </div>

                <!-- ROW 3: Amount -->
                <mat-form-field appearance="outline" class="full-width">
                  <mat-label>{{ settings.labels().amountEur }}</mat-label>
                  <input matInput type="number" formControlName="amount"
                         step="0.01" min="0.01" #amountInput>
                  <span matTextPrefix>&euro;&nbsp;</span>
                </mat-form-field>

                <!-- Type Indicator Banner (sub-component) -->
                @if (currentTypeDisplay()) {
                  <app-type-indicator [typeDisplay]="currentTypeDisplay()" />
                }

                <!-- ROW 4: Category (optional) + Subcategory -->
                <div class="form-row two-col">
                  <mat-form-field appearance="outline">
                    <mat-label>{{ settings.labels().categoryOptional }}</mat-label>
                    <mat-select formControlName="categoryId"
                                (selectionChange)="onCategoryChange($event.value)">
                      <mat-option [value]="null">{{ settings.labels().clearCategory }}</mat-option>
                      @for (cat of filteredCategories(); track cat.id) {
                        <mat-option [value]="cat.id">{{ cat.name }}</mat-option>
                      }
                    </mat-select>
                  </mat-form-field>

                  <mat-form-field appearance="outline">
                    <mat-label>{{ settings.labels().subcategoryOptional }}</mat-label>
                    <mat-select formControlName="subcategoryId">
                      <mat-option [value]="null">&mdash;</mat-option>
                      @for (sub of subcategories(); track sub.id) {
                        <mat-option [value]="sub.id">{{ sub.name }}</mat-option>
                      }
                    </mat-select>
                  </mat-form-field>
                </div>

                <!-- ROW 5: Description, Tags, Detail -->
                <mat-form-field appearance="outline" class="full-width">
                  <mat-label>{{ settings.labels().notes }}</mat-label>
                  <textarea matInput formControlName="bankDescription" rows="2"></textarea>
                </mat-form-field>

                <mat-form-field appearance="outline" class="full-width">
                  <mat-label>{{ settings.labels().tags }}</mat-label>
                  <mat-select formControlName="tagIds" multiple>
                    @for (tag of activeTags(); track tag.id) {
                      <mat-option [value]="tag.id">{{ tag.name }}</mat-option>
                    }
                  </mat-select>
                </mat-form-field>

                <mat-form-field appearance="outline" class="full-width">
                  <mat-label>{{ settings.labels().detail }}</mat-label>
                  <input matInput formControlName="detail">
                </mat-form-field>

                <!-- ROW 6: Additional Details (collapsible) -->
                <mat-expansion-panel [expanded]="expandAdditionalDetails()">
                  <mat-expansion-panel-header>
                    <mat-panel-title>
                      {{ settings.labels().additionalDetails }}
                    </mat-panel-title>
                  </mat-expansion-panel-header>

                  <div class="form-row two-col">
                    <mat-form-field appearance="outline">
                      <mat-label>{{ settings.labels().counterpartyName }}</mat-label>
                      <input matInput formControlName="counterpartyName">
                    </mat-form-field>
                    <mat-form-field appearance="outline">
                      <mat-label>{{ settings.labels().counterpartyReference }}</mat-label>
                      <input matInput formControlName="counterpartyReference">
                    </mat-form-field>
                  </div>

                  <mat-form-field appearance="outline" class="full-width">
                    <mat-label>{{ settings.labels().sourceReference }}</mat-label>
                    <input matInput formControlName="sourceReference">
                  </mat-form-field>
                </mat-expansion-panel>

                <!-- Notes Section (edit mode — sub-component) -->
                @if (isEdit && editTx()) {
                  <app-transaction-notes
                    [transactionId]="transactionId!"
                    [year]="editYear"
                    [month]="editMonth"
                    [initialNotes]="sortedNotes()" />
                }

                <!-- Review Status (edit mode — sub-component) -->
                @if (isEdit && editTx()) {
                  <app-transaction-review
                    [transactionId]="transactionId!"
                    [year]="editYear"
                    [month]="editMonth"
                    [currentStatus]="editTx()!.reviewStatus"
                    [reviewedByName]="editTx()!.reviewedByName ?? null"
                    [reviewedAt]="editTx()!.reviewedAt ?? null"
                    [isAdmin]="authService.isAdmin()"
                    (statusChanged)="editTx.set($event)" />
                }

                <!-- Actions -->
                <div class="form-actions">
                  <button mat-button type="button" (click)="router.navigate(['/transactions'])">
                    {{ settings.labels().cancel }}
                  </button>
                  <button mat-flat-button color="primary" type="submit"
                          [disabled]="form.invalid || saving()">
                    {{ saving() ? settings.labels().saving : (isEdit ? settings.labels().update : settings.labels().saveAndNew) }}
                  </button>
                </div>
              </form>
            </mat-card-content>
          </mat-card>
        </app-loading-container>
      }
    </div>
  `,
  styles: `
    .form-card { max-width: 800px; }
    .form-row { margin-bottom: var(--spc-8); }
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spc-16); }
    .three-col { display: grid; grid-template-columns: 1fr 1fr auto; gap: var(--spc-16); align-items: center; }
    .full-width { width: 100%; }
    .form-actions {
      display: flex;
      justify-content: flex-end;
      gap: var(--spc-12);
      margin-top: var(--spc-16);
    }
    .currency-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: var(--spc-6) var(--spc-16);
      border-radius: var(--rad-pill);
      font-size: var(--font-sm);
      font-weight: var(--fw-medium);
      background: var(--clr-transfer-bg);
      color: var(--clr-transfer);
      height: 56px;
      margin-top: var(--spc-4);
    }
    mat-expansion-panel { margin-bottom: var(--spc-16); }
  `,
})
export class TransactionFormComponent implements OnInit {
  readonly router = inject(Router);
  readonly settings = inject(AppSettingsService);
  readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly transactionService = inject(TransactionService);
  readonly refData = inject(ReferenceDataService);
  private readonly snackBar = inject(MatSnackBar);

  readonly amountInput = viewChild<ElementRef>('amountInput');

  readonly loadingForm = signal(true);
  readonly loadError = signal(false);
  readonly saving = signal(false);
  readonly subcategories = signal<Subcategory[]>([]);
  readonly expandAdditionalDetails = signal(false);

  // --- Type display tracking ---
  readonly currentTypeDisplay = signal<TransactionTypeDisplay | ''>('');

  readonly typeOptions = computed(() => {
    const l = this.settings.labels();
    return [
      { value: 'income', label: l.incomeOption },
      { value: 'expense', label: l.expenseOption },
      { value: 'transfer_in', label: l.transferInOption },
      { value: 'transfer_out', label: l.transferOutOption },
      { value: 'refund_received', label: l.refundReceivedOption },
      { value: 'refund_given', label: l.refundGivenOption },
    ];
  });

  readonly filteredCategories = computed(() => {
    return this.refData.categories().filter(c => c.isActive);
  });

  readonly activeAccounts = computed(() =>
    this.refData.accounts().filter(a => a.isActive),
  );
  readonly activeTags = computed(() =>
    this.refData.tags().filter(t => t.isActive),
  );

  // --- Edit mode state ---
  readonly editTx = signal<Transaction | null>(null);

  readonly sortedNotes = computed(() => {
    const tx = this.editTx();
    if (!tx?.notes) return [];
    return [...tx.notes].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    );
  });

  isEdit = false;
  transactionId: string | null = null;
  editYear = 0;
  editMonth = 0;

  form: FormGroup = this.fb.group({
    transactionTypeDisplay: ['', Validators.required],
    accountId: [localStorage.getItem(LAST_ACCOUNT_KEY) ?? '', Validators.required],
    date: [new Date(), Validators.required],
    valueDate: [null],
    amount: [null, [Validators.required, Validators.min(0.01)]],
    bankDescription: [''],
    categoryId: [null as string | null],
    subcategoryId: [null as string | null],
    tagIds: [[] as string[]],
    detail: [''],
    counterpartyName: [''],
    counterpartyReference: [''],
    sourceReference: [''],
  });

  ngOnInit(): void {
    this.transactionId = this.route.snapshot.paramMap.get('id');
    this.isEdit = !!this.transactionId;
    this.editYear = Number(this.route.snapshot.queryParamMap.get('year')) || 0;
    this.editMonth = Number(this.route.snapshot.queryParamMap.get('month')) || 0;
    this.refData.load();

    if (this.isEdit && this.transactionId) {
      this.loadTransaction(this.transactionId);
    } else {
      this.loadingForm.set(false);
    }
  }

  // --- Type change handler ---
  onTypeChange(typeDisplay: TransactionTypeDisplay): void {
    this.currentTypeDisplay.set(typeDisplay);
  }

  onCategoryChange(categoryId: string | null): void {
    if (!categoryId) {
      this.subcategories.set([]);
      this.form.patchValue({ subcategoryId: null });
      return;
    }
    const cat = this.refData.categories().find(c => c.id === categoryId);
    this.subcategories.set(cat?.subcategories?.filter(s => s.isActive) ?? []);
    if (!cat?.subcategories?.find(s => s.id === this.form.value.subcategoryId)) {
      this.form.patchValue({ subcategoryId: null });
    }
  }

  retryLoad(): void {
    if (this.transactionId) {
      this.loadError.set(false);
      this.loadingForm.set(true);
      this.loadTransaction(this.transactionId);
    }
  }

  /** Save and return to list */
  onSave(): void {
    if (this.form.invalid) return;
    this.saving.set(true);
    this.persist().subscribe({
      next: () => {
        this.snackBar.open(this.settings.labels().transactionSaved, '', { duration: 2500 });
        this.router.navigate(['/transactions']);
      },
      error: () => this.saving.set(false),
    });
  }

  /** Save and reset form for another entry (primary action) */
  onSaveAndNew(): void {
    if (this.form.invalid || this.saving()) return;
    if (this.isEdit) {
      this.onSave();
      return;
    }
    this.saving.set(true);
    this.persist().subscribe({
      next: () => {
        this.snackBar.open(this.settings.labels().transactionSaved, '', { duration: 2500 });
        const keepAccount = this.form.value.accountId;
        const keepDate = this.form.value.date;
        const keepType = this.form.value.transactionTypeDisplay;
        this.form.reset({
          transactionTypeDisplay: keepType,
          accountId: keepAccount,
          date: keepDate,
          tagIds: [],
        });
        this.currentTypeDisplay.set(keepType);
        this.subcategories.set([]);
        this.saving.set(false);
        setTimeout(() => this.amountInput()?.nativeElement?.focus());
      },
      error: () => this.saving.set(false),
    });
  }

  private loadTransaction(id: string): void {
    this.transactionService.get(id, this.editYear, this.editMonth).subscribe({
      next: (tx) => {
        this.editTx.set(tx);
        const typeDisplay = this.deriveTypeDisplay(tx);
        this.currentTypeDisplay.set(typeDisplay);

        this.form.patchValue({
          transactionTypeDisplay: typeDisplay,
          accountId: tx.accountId,
          date: new Date(tx.date),
          valueDate: tx.valueDate ? new Date(tx.valueDate) : null,
          amount: Math.abs(tx.amount),
          bankDescription: tx.bankDescription,
          categoryId: tx.categoryId,
          subcategoryId: tx.subcategoryId,
          tagIds: tx.tagIds ?? [],
          detail: tx.detail,
          counterpartyName: tx.counterpartyName,
          counterpartyReference: tx.counterpartyReference,
          sourceReference: tx.sourceReference,
        });

        if (tx.categoryId) {
          this.onCategoryChange(tx.categoryId);
        }

        // Auto-expand additional details if any field is populated
        if (tx.counterpartyName || tx.counterpartyReference || tx.sourceReference) {
          this.expandAdditionalDetails.set(true);
        }

        this.loadingForm.set(false);
      },
      error: () => {
        this.loadError.set(true);
        this.loadingForm.set(false);
      },
    });
  }

  private deriveTypeDisplay(tx: Transaction): TransactionTypeDisplay {
    switch (tx.transactionType) {
      case 'income': return 'income';
      case 'expense': return 'expense';
      case 'transfer': return tx.amount >= 0 ? 'transfer_in' : 'transfer_out';
      case 'refund': return tx.amount >= 0 ? 'refund_received' : 'refund_given';
      default: return 'income';
    }
  }

  private persist() {
    const v = this.form.value;
    if (v.accountId) {
      localStorage.setItem(LAST_ACCOUNT_KEY, v.accountId);
    }

    const mapping = TYPE_MAP[v.transactionTypeDisplay as TransactionTypeDisplay];
    const signedAmount = Math.abs(v.amount) * mapping.sign;

    const payload: TransactionCreate = {
      accountId: v.accountId,
      transactionType: mapping.transactionType,
      date: this.formatDate(v.date),
      valueDate: v.valueDate ? this.formatDate(v.valueDate) : undefined,
      amount: signedAmount,
      bankDescription: v.bankDescription || undefined,
      categoryId: v.categoryId || null,
      subcategoryId: v.subcategoryId || null,
      tagIds: v.tagIds?.length ? v.tagIds : undefined,
      detail: v.detail || undefined,
      counterpartyName: v.counterpartyName || undefined,
      counterpartyReference: v.counterpartyReference || undefined,
      sourceReference: v.sourceReference || undefined,
    };

    return this.isEdit && this.transactionId
      ? this.transactionService.update(this.transactionId, payload, this.editYear, this.editMonth)
      : this.transactionService.create(payload);
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}
