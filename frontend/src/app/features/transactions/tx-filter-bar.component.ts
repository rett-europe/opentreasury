import { ChangeDetectionStrategy, Component, computed, inject, OnInit, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { AppSettingsService } from '@core/services/app-settings.service';
import { ReferenceDataService } from '@core/services/reference-data.service';

// --- Preset date range helpers (pure, testable) ---

export interface DateRange { from: Date; to: Date }

export function getThisMonth(): DateRange {
  const now = new Date();
  return { from: new Date(now.getFullYear(), now.getMonth(), 1), to: now };
}

export function getLastMonth(): DateRange {
  const now = new Date();
  const y = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
  const m = now.getMonth() === 0 ? 11 : now.getMonth() - 1;
  return { from: new Date(y, m, 1), to: new Date(y, m + 1, 0) };
}

export function getLast30Days(): DateRange {
  const now = new Date();
  const from = new Date(now);
  from.setDate(from.getDate() - 30);
  return { from, to: now };
}

export function getThisQuarter(): DateRange {
  const now = new Date();
  const qStart = Math.floor(now.getMonth() / 3) * 3;
  return { from: new Date(now.getFullYear(), qStart, 1), to: now };
}

export function getLastQuarter(): DateRange {
  const now = new Date();
  const currentQStart = Math.floor(now.getMonth() / 3) * 3;
  const prevQStart = currentQStart - 3;
  const y = prevQStart < 0 ? now.getFullYear() - 1 : now.getFullYear();
  const m = prevQStart < 0 ? prevQStart + 12 : prevQStart;
  return { from: new Date(y, m, 1), to: new Date(y, m + 3, 0) };
}

export function getThisYear(): DateRange {
  const now = new Date();
  return { from: new Date(now.getFullYear(), 0, 1), to: now };
}

export function getLastYear(): DateRange {
  const now = new Date();
  const y = now.getFullYear() - 1;
  return { from: new Date(y, 0, 1), to: new Date(y, 11, 31) };
}

const PRESET_FNS: Record<string, () => DateRange> = {
  'this-month': getThisMonth,
  'last-month': getLastMonth,
  'last-30-days': getLast30Days,
  'this-quarter': getThisQuarter,
  'last-quarter': getLastQuarter,
  'this-year': getThisYear,
  'last-year': getLastYear,
};

function toIsoDate(d: Date): string {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

export interface TransactionFilters {
  dateFrom: string | null;
  dateTo: string | null;
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
    MatButtonModule,
    MatButtonToggleModule,
    MatDatepickerModule,
    MatNativeDateModule,
  ],
  template: `
    <div class="filter-bar">
      <!-- ROW 0: Preset strip -->
      <div class="filter-preset-strip">
        <mat-button-toggle-group [value]="activePreset()" (change)="onPresetChange($event.value)"
                                 class="preset-group" hideSingleSelectionIndicator>
          <mat-button-toggle value="this-month">{{ settings.labels().presetThisMonth }}</mat-button-toggle>
          <mat-button-toggle value="last-month">{{ settings.labels().presetLastMonth }}</mat-button-toggle>
          <mat-button-toggle value="last-30-days">{{ settings.labels().presetLast30Days }}</mat-button-toggle>
          <mat-button-toggle value="this-quarter">{{ settings.labels().presetThisQuarter }}</mat-button-toggle>
          <mat-button-toggle value="last-quarter">{{ settings.labels().presetLastQuarter }}</mat-button-toggle>
          <mat-button-toggle value="this-year">{{ settings.labels().presetThisYear }}</mat-button-toggle>
          <mat-button-toggle value="last-year">{{ settings.labels().presetLastYear }}</mat-button-toggle>
        </mat-button-toggle-group>
        <div class="preset-strip-actions">
          @if (dateFrom || dateTo) {
            <button mat-stroked-button class="clear-btn" (click)="clearDateRange()">
              <mat-icon>close</mat-icon>
              {{ settings.labels().clearDateRange }}
            </button>
          }

          <button mat-stroked-button class="uncat-preset-btn" (click)="onShowUncategorized()">
            <mat-icon>label_off</mat-icon>
            {{ settings.labels().showAllUncategorized }}
          </button>
        </div>
      </div>

      <!-- ROW 1: Primary filters (date range replaces year/month) -->
      <div class="filter-row">
        <mat-form-field appearance="outline" class="filter-field-date">
          <mat-label>{{ settings.labels().dateFrom }} — {{ settings.labels().dateTo }}</mat-label>
          <mat-date-range-input [rangePicker]="picker">
            <input matStartDate [ngModel]="dateFrom" (dateChange)="onManualDateChange($event.value, 'from')"
                   [placeholder]="settings.labels().dateFrom">
            <input matEndDate [ngModel]="dateTo" (dateChange)="onManualDateChange($event.value, 'to')"
                   [placeholder]="settings.labels().dateTo">
          </mat-date-range-input>
          <mat-datepicker-toggle matIconSuffix [for]="picker" />
          <mat-date-range-picker #picker />
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

      <!-- ROW 2: Secondary filters -->
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
    .filter-preset-strip {
      display: flex;
      align-items: center;
      gap: var(--spc-8);
      padding-bottom: var(--spc-12);
      margin-bottom: var(--spc-8);
      border-bottom: 1px solid var(--clr-divider);
      flex-wrap: wrap;
    }
    .preset-group {
      border-radius: var(--rad-pill);
      border: 1px solid var(--clr-border);
    }
    :host ::ng-deep .preset-group .mat-button-toggle-appearance-standard {
      background: transparent;
      color: var(--clr-text-secondary);
      font-size: var(--font-sm);
      font-weight: var(--fw-medium);
    }
    :host ::ng-deep .preset-group .mat-button-toggle-checked .mat-button-toggle-appearance-standard {
      background: var(--brand-primary);
      color: var(--brand-on-primary);
      font-weight: var(--fw-semibold);
    }
    :host ::ng-deep .preset-group .mat-button-toggle-appearance-standard:hover:not(.mat-button-toggle-disabled) {
      background: var(--brand-surface-hover);
      color: var(--clr-text-primary);
    }
    :host ::ng-deep .preset-group .mat-button-toggle-checked .mat-button-toggle-appearance-standard:hover {
      background: var(--brand-primary);
      color: var(--brand-on-primary);
    }
    .preset-strip-actions {
      margin-left: auto;
      display: flex;
      gap: var(--spc-8);
      align-items: center;
    }
    .clear-btn {
      color: var(--clr-text-muted);
      border-color: var(--clr-border);
    }
    .uncat-preset-btn {
      white-space: nowrap;
      font-size: var(--font-sm);
      font-weight: var(--fw-medium);
      color: var(--clr-text-secondary);
      border-color: var(--clr-border);
    }
    .uncat-preset-btn:hover {
      background: var(--brand-surface-hover, rgba(0, 0, 0, 0.04));
      color: var(--clr-text-primary);
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
    .filter-field-date {
      width: 260px;
      min-width: 220px;
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
  readonly showUncategorized = output<void>();

  readonly activePreset = signal<string | null>(null);

  dateFrom: Date | null = null;
  dateTo: Date | null = null;
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

  private readonly selectedCategoryId = signal<string | null>(null);

  readonly filterSubcategories = computed(() => {
    const catId = this.selectedCategoryId();
    if (!catId) return [];
    const cat = this.refData.categories().find(c => c.id === catId);
    return cat?.subcategories?.filter(s => s.isActive) ?? [];
  });

  ngOnInit(): void {
    // Page starts empty — emit null dates so transaction-list knows no range is selected
    this.emitFilters();
  }

  onPresetChange(value: string): void {
    const fn = PRESET_FNS[value];
    if (!fn) return;
    const range = fn();
    this.dateFrom = range.from;
    this.dateTo = range.to;
    this.activePreset.set(value);
    this.emitFilters();
  }

  /** Apply a preset by key — called from inline shortcut chips in the empty state */
  applyPreset(key: string): void {
    this.onPresetChange(key);
  }

  /** Clear date filters and enter uncategorized mode */
  onShowUncategorized(): void {
    this.dateFrom = null;
    this.dateTo = null;
    this.activePreset.set(null);
    this.showUncategorized.emit();
  }

  onManualDateChange(value: Date | null, field: 'from' | 'to'): void {
    if (field === 'from') {
      this.dateFrom = value;
    } else {
      this.dateTo = value;
    }
    // Deselect any preset when user manually edits
    this.activePreset.set(null);
    // Emit when both dates are set, OR when a previously-complete range becomes incomplete
    this.emitFilters();
  }

  clearDateRange(): void {
    this.dateFrom = null;
    this.dateTo = null;
    this.activePreset.set(null);
    this.emitFilters();
  }

  onCategoryChange(): void {
    this.selectedCategoryId.set(this.categoryId);
    this.subcategoryId = null;
    this.emitFilters();
  }

  emitFilters(): void {
    this.filtersChanged.emit({
      dateFrom: this.dateFrom ? toIsoDate(this.dateFrom) : null,
      dateTo: this.dateTo ? toIsoDate(this.dateTo) : null,
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
