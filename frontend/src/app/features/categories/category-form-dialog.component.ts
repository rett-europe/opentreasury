import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import {
  FormArray,
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AppSettingsService } from '@core/services/app-settings.service';
import { CategoryService } from '@core/services/category.service';
import { Category, CATEGORY_TYPES } from '@shared/models/category.model';

@Component({
  selector: 'app-category-form-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="dialog-header">
      <div class="dialog-title-row">
        <mat-icon class="title-icon">category</mat-icon>
        <h2 mat-dialog-title>{{ data ? settings.labels().editCategory : settings.labels().newCategory }}</h2>
      </div>
      <button mat-icon-button mat-dialog-close class="close-btn" aria-label="Close">
        <mat-icon>close</mat-icon>
      </button>
    </div>

    <mat-dialog-content>
      <form [formGroup]="form">
        <!-- Type toggle cards -->
        <div class="type-toggle-cards">
          <button type="button" class="type-card income"
                  [class.selected]="form.value.categoryType === CATEGORY_TYPES.INCOME"
                  (click)="form.patchValue({ categoryType: CATEGORY_TYPES.INCOME })">
            <mat-icon>arrow_upward</mat-icon>
            <span>{{ settings.labels().incomeType }}</span>
          </button>
          <button type="button" class="type-card expense"
                  [class.selected]="form.value.categoryType === CATEGORY_TYPES.EXPENSE"
                  (click)="form.patchValue({ categoryType: CATEGORY_TYPES.EXPENSE })">
            <mat-icon>arrow_downward</mat-icon>
            <span>{{ settings.labels().expenseType }}</span>
          </button>
        </div>

        <!-- Name -->
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>{{ settings.labels().name }}</mat-label>
          <input matInput formControlName="name">
        </mat-form-field>

        <!-- Description -->
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>{{ settings.labels().description }}</mat-label>
          <input matInput formControlName="description">
        </mat-form-field>

        <!-- Subcategories section -->
        <div class="subcategories-section">
          <div class="section-header">
            <div class="section-title-row">
              <strong>{{ settings.labels().subcategories }}</strong>
              <span class="count-badge">{{ subcategoriesArray.length }}</span>
            </div>
          </div>
          <div class="subcategories-container" [class.empty]="subcategoriesArray.length === 0">
            <div formArrayName="subcategories">
              @for (sub of subcategoriesArray.controls; track sub; let i = $index) {
                <div class="subcategory-row" [formGroupName]="i">
                  <span class="sub-index">{{ i + 1 }}</span>
                  <mat-form-field appearance="outline" class="sub-field">
                    <input matInput formControlName="name" [placeholder]="settings.labels().subcategoryName">
                  </mat-form-field>
                  <button mat-icon-button type="button" class="remove-btn" (click)="removeSubcategory(i)">
                    <mat-icon>close</mat-icon>
                  </button>
                </div>
              }
            </div>
            @if (subcategoriesArray.length === 0) {
              <span class="empty-state-text">{{ settings.labels().noSubcategoriesYet }}</span>
            }
            <div class="add-subcategory-row">
              <mat-form-field appearance="outline" class="sub-field">
                <input matInput [(ngModel)]="newSubName" [ngModelOptions]="{ standalone: true }"
                       [placeholder]="settings.labels().subcategoryName"
                       (keydown.enter)="addSubcategoryFromInput(); $event.preventDefault()">
              </mat-form-field>
              <button mat-stroked-button type="button" (click)="addSubcategoryFromInput()"
                      [disabled]="!newSubName.trim()">
                <mat-icon>add</mat-icon>
                {{ settings.labels().addSubcategory }}
              </button>
            </div>
          </div>
        </div>

        <!-- Active toggle (edit mode only) -->
        @if (data) {
          <div class="active-toggle-row">
            <mat-slide-toggle formControlName="isActive">
              {{ settings.labels().activeCategory }}
            </mat-slide-toggle>
          </div>
        }
      </form>
    </mat-dialog-content>

    <mat-dialog-actions>
      <button mat-button mat-dialog-close>{{ settings.labels().cancel }}</button>
      <span class="action-spacer"></span>
      <button mat-flat-button color="primary" (click)="onSave()"
              [disabled]="form.invalid || saving()">
        @if (saving()) {
          <mat-spinner diameter="18" class="btn-spinner"></mat-spinner>
        }
        {{ saving() ? settings.labels().saving : settings.labels().save }}
      </button>
    </mat-dialog-actions>
  `,
  styles: `
    :host ::ng-deep .mat-mdc-dialog-content {
      max-height: none;
      overflow: visible;
    }

    /* --- Dialog header --- */
    .dialog-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--spc-16) var(--spc-24) 0;
    }
    .dialog-title-row {
      display: flex;
      align-items: center;
      gap: var(--spc-8);
    }
    .title-icon {
      color: var(--brand-primary);
      font-size: 22px;
      width: 22px;
      height: 22px;
      line-height: 1;
    }
    h2[mat-dialog-title] {
      margin: 0;
      padding: 0;
      font-size: 18px;
      font-weight: var(--fw-semibold);
      line-height: 22px;
    }
    .close-btn {
      color: var(--clr-text-muted);
    }

    /* --- Type toggle cards --- */
    .type-toggle-cards {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--spc-12);
      margin-bottom: var(--spc-20);
    }
    .type-card {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spc-8);
      padding: var(--spc-12) var(--spc-16);
      border-radius: var(--rad-md);
      border: 2px solid var(--clr-border);
      background: var(--clr-surface);
      cursor: pointer;
      font-size: var(--font-body);
      font-weight: var(--fw-medium);
      transition: all var(--transition-fast);
      color: var(--clr-text-secondary);
    }
    .type-card:hover {
      border-color: var(--clr-text-muted);
    }
    .type-card.income.selected {
      border-color: var(--clr-income);
      background: var(--clr-income-bg);
      color: var(--clr-income-on-bg);
    }
    .type-card.expense.selected {
      border-color: var(--clr-expense);
      background: var(--clr-expense-bg);
      color: var(--clr-expense-on-bg);
    }

    /* --- Subcategories --- */
    .subcategories-section {
      margin-top: var(--spc-8);
    }
    .section-header {
      margin-bottom: var(--spc-8);
    }
    .section-title-row {
      display: flex;
      align-items: center;
      gap: var(--spc-8);
    }
    .count-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 22px;
      height: 22px;
      border-radius: var(--rad-round);
      background: var(--brand-surface);
      color: var(--brand-primary);
      font-size: var(--font-xs);
      font-weight: var(--fw-semibold);
      padding: 0 var(--spc-4);
    }
    .subcategories-container {
      border: 1px solid var(--clr-border);
      border-radius: var(--rad-md);
      background: var(--clr-surface-panel);
      padding: var(--spc-12);
    }
    .subcategories-container.empty {
      border-style: dashed;
    }
    .subcategory-row {
      display: flex;
      align-items: center;
      gap: var(--spc-6);
      margin-bottom: var(--spc-4);
    }
    .sub-index {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--brand-surface);
      color: var(--brand-primary);
      font-size: 11px;
      font-weight: var(--fw-semibold);
      flex-shrink: 0;
    }
    .sub-field {
      flex: 1;
    }
    .sub-field ::ng-deep .mat-mdc-form-field-subscript-wrapper {
      display: none;
    }
    .remove-btn {
      color: var(--clr-text-muted);
    }
    .remove-btn:hover {
      color: var(--clr-expense);
    }
    .empty-state-text {
      display: block;
      text-align: center;
      padding: var(--spc-12) 0;
      color: var(--clr-text-disabled);
      font-style: italic;
      font-size: var(--font-sm);
    }
    .add-subcategory-row {
      display: flex;
      gap: var(--spc-8);
      align-items: center;
      margin-top: var(--spc-8);
      padding-top: var(--spc-8);
      border-top: 1px solid var(--clr-divider);
    }

    /* --- Active toggle --- */
    .active-toggle-row {
      margin-top: var(--spc-16);
      padding-top: var(--spc-16);
      border-top: 1px solid var(--clr-divider);
    }

    /* --- Actions --- */
    mat-dialog-actions {
      display: flex;
      padding: var(--spc-12) var(--spc-24) var(--spc-16);
    }
    .action-spacer {
      flex: 1;
    }
    .btn-spinner {
      display: inline-block;
      margin-right: var(--spc-8);
      vertical-align: middle;
    }
    .btn-spinner ::ng-deep circle {
      stroke: var(--brand-on-primary);
    }
  `,
})
export class CategoryFormDialogComponent {
  readonly CATEGORY_TYPES = CATEGORY_TYPES;
  readonly data = inject<Category | null>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<CategoryFormDialogComponent>);
  private readonly fb = inject(FormBuilder);
  private readonly categoryService = inject(CategoryService);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);

  readonly saving = signal(false);
  newSubName = '';

  form: FormGroup = this.fb.group({
    categoryType: [this.data?.categoryType ?? '', Validators.required],
    name: [this.data?.name ?? '', Validators.required],
    description: [this.data?.description ?? ''],
    isActive: [this.data?.isActive ?? true],
    subcategories: this.fb.array(
      (this.data?.subcategories ?? []).map((s) =>
        this.fb.group({ id: [s.id], name: [s.name, Validators.required] })
      )
    ),
  });

  get subcategoriesArray(): FormArray {
    return this.form.get('subcategories') as FormArray;
  }

  addSubcategoryFromInput(): void {
    const name = this.newSubName.trim();
    if (!name) return;
    this.subcategoriesArray.push(
      this.fb.group({ id: [null], name: [name, Validators.required] })
    );
    this.newSubName = '';
  }

  removeSubcategory(index: number): void {
    this.subcategoriesArray.removeAt(index);
  }

  onSave(): void {
    if (this.form.invalid) return;
    this.saving.set(true);

    const payload = this.form.value;
    const obs = this.data
      ? this.categoryService.update(this.data.id, payload)
      : this.categoryService.create(payload);

    obs.subscribe({
      next: () => this.dialogRef.close(true),
      error: (err) => {
        this.saving.set(false);
        const msg = err?.error?.detail || this.settings.labels().categorySaveError;
        this.snackBar.open(msg, this.settings.labels().close, { duration: 6000, panelClass: 'error-snack' });
      },
    });
  }
}
