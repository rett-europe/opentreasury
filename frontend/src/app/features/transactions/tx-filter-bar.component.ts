import { ChangeDetectionStrategy, Component, computed, inject, OnInit, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { AppSettingsService } from '@core/services/app-settings.service';
import { ReferenceDataService } from '@core/services/reference-data.service';

export interface TransactionFilters {
  year: number;
  month: number | null;
  accountId: string | null;
  categoryId: string | null;
  subcategoryId: string | null;
  tagId: string | null;
  transactionType: string | null;
  categorizationStatus: string | null;
  reviewStatus: string | null;
  search: string | null;
  amountMin: number | null;
  amountMax: number | null;
}

@Component({
  selector: 'app-tx-filter-bar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatIconModule,
  ],
  template: `
    <div class="filter-bar">
      <div class="filter-row">
        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().year }}</mat-label>
          <mat-select [(ngModel)]="year" (selectionChange)="emitFilters()">
            @for (y of years; track y) {
              <mat-option [value]="y">{{ y }}</mat-option>
            }
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().month }}</mat-label>
          <mat-select [(ngModel)]="month" (selectionChange)="emitFilters()">
            <mat-option [value]="null">{{ settings.labels().allMonths }}</mat-option>
            @for (m of monthOptions(); track m.value) {
              <mat-option [value]="m.value">{{ m.label }}</mat-option>
            }
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().account }}</mat-label>
          <mat-select [(ngModel)]="accountId" (selectionChange)="emitFilters()">
            <mat-option [value]="null">{{ settings.labels().allItems }}</mat-option>
            @for (acc of refData.accounts(); track acc.id) {
              @if (acc.isActive) {
                <mat-option [value]="acc.id">{{ acc.accountLabel }}</mat-option>
              }
            }
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().category }}</mat-label>
          <mat-select [(ngModel)]="categoryId" (selectionChange)="onCategoryChange()">
            <mat-option [value]="null">{{ settings.labels().allItems }}</mat-option>
            @for (cat of refData.categories(); track cat.id) {
              @if (cat.isActive) {
                <mat-option [value]="cat.id">{{ cat.name }}</mat-option>
              }
            }
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().subcategory }}</mat-label>
          <mat-select [(ngModel)]="subcategoryId" (selectionChange)="emitFilters()"
                      [disabled]="!categoryId">
            <mat-option [value]="null">{{ settings.labels().allItems }}</mat-option>
            @for (sub of filterSubcategories(); track sub.id) {
              <mat-option [value]="sub.id">{{ sub.name }}</mat-option>
            }
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().tag }}</mat-label>
          <mat-select [(ngModel)]="tagId" (selectionChange)="emitFilters()">
            <mat-option [value]="null">{{ settings.labels().allItems }}</mat-option>
            @for (tag of refData.tags(); track tag.id) {
              @if (tag.isActive) {
                <mat-option [value]="tag.id">{{ tag.name }}</mat-option>
              }
            }
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().transactionType }}</mat-label>
          <mat-select [(ngModel)]="transactionType" (selectionChange)="emitFilters()">
            <mat-option [value]="null">{{ settings.labels().allItems }}</mat-option>
            <mat-option value="income">{{ settings.labels().incomeType }}</mat-option>
            <mat-option value="expense">{{ settings.labels().expenseType }}</mat-option>
            <mat-option value="transfer">{{ settings.labels().transferType }}</mat-option>
            <mat-option value="refund">{{ settings.labels().refundType }}</mat-option>
          </mat-select>
        </mat-form-field>
      </div>

      <div class="filter-row">
        <mat-form-field appearance="outline" class="filter-field search-field">
          <mat-label>{{ settings.labels().search }}</mat-label>
          <input matInput [(ngModel)]="search"
                 (ngModelChange)="emitFilters()"
                 [placeholder]="settings.labels().searchPlaceholder">
          <mat-icon matSuffix>search</mat-icon>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field-sm">
          <mat-label>{{ settings.labels().minAmount }}</mat-label>
          <input matInput type="number" [(ngModel)]="amountMin"
                 (ngModelChange)="emitFilters()">
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field-sm">
          <mat-label>{{ settings.labels().maxAmount }}</mat-label>
          <input matInput type="number" [(ngModel)]="amountMax"
                 (ngModelChange)="emitFilters()">
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().categorizationFilter }}</mat-label>
          <mat-select [(ngModel)]="categorizationStatus" (selectionChange)="emitFilters()">
            <mat-option [value]="null">{{ settings.labels().allItems }}</mat-option>
            <mat-option value="uncategorized">{{ settings.labels().uncategorizedOnly }}</mat-option>
            <mat-option value="manually_categorized">{{ settings.labels().manuallyCategorized }}</mat-option>
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>{{ settings.labels().reviewStatusFilter }}</mat-label>
          <mat-select [(ngModel)]="reviewStatus" (selectionChange)="emitFilters()">
            <mat-option [value]="null">{{ settings.labels().allItems }}</mat-option>
            <mat-option value="pending">{{ settings.labels().statusPending }}</mat-option>
            <mat-option value="reviewed">{{ settings.labels().statusReviewed }}</mat-option>
            <mat-option value="approved">{{ settings.labels().statusApproved }}</mat-option>
            <mat-option value="flagged">{{ settings.labels().statusFlagged }}</mat-option>
          </mat-select>
        </mat-form-field>
      </div>
    </div>
  `,
  styles: `
    .filter-bar {
      background: var(--clr-surface);
      border-radius: var(--rad-lg);
      box-shadow: var(--elev-card);
      padding: var(--spc-16) var(--spc-20);
      margin-bottom: var(--spc-16);
    }
    .filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: var(--spc-12);
      align-items: center;
      margin-bottom: var(--spc-8);
    }
    .filter-row:last-child {
      margin-bottom: 0;
    }
    .filter-field {
      width: 160px;
    }
    .filter-field-sm {
      width: 130px;
    }
    .search-field {
      flex: 1;
      min-width: 200px;
    }
  `,
})
export class TransactionFilterBarComponent implements OnInit {
  readonly settings = inject(AppSettingsService);
  readonly refData = inject(ReferenceDataService);

  readonly filtersChanged = output<TransactionFilters>();

  year = new Date().getFullYear();
  month: number | null = null;
  accountId: string | null = null;
  categoryId: string | null = null;
  subcategoryId: string | null = null;
  tagId: string | null = null;
  transactionType: string | null = null;
  categorizationStatus: string | null = null;
  reviewStatus: string | null = null;
  search: string | null = null;
  amountMin: number | null = null;
  amountMax: number | null = null;

  readonly years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  readonly monthOptions = computed(() =>
    this.settings.labels().monthNames.map((label: string, i: number) => ({ value: i + 1, label }))
  );

  private readonly selectedCategoryId = signal<string | null>(null);

  readonly filterSubcategories = computed(() => {
    const catId = this.selectedCategoryId();
    if (!catId) return [];
    const cat = this.refData.categories().find(c => c.id === catId);
    return cat?.subcategories?.filter(s => s.isActive) ?? [];
  });

  ngOnInit(): void {
    this.emitFilters();
  }

  onCategoryChange(): void {
    this.selectedCategoryId.set(this.categoryId);
    this.subcategoryId = null;
    this.emitFilters();
  }

  emitFilters(): void {
    this.filtersChanged.emit({
      year: this.year,
      month: this.month,
      accountId: this.accountId,
      categoryId: this.categoryId,
      subcategoryId: this.subcategoryId,
      tagId: this.tagId,
      transactionType: this.transactionType,
      categorizationStatus: this.categorizationStatus,
      reviewStatus: this.reviewStatus,
      search: this.search,
      amountMin: this.amountMin,
      amountMax: this.amountMax,
    });
  }
}
