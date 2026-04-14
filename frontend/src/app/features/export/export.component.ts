import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { AppSettingsService } from '@core/services/app-settings.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { ExportService, ExportParams } from '@core/services/export.service';
import { PageHeaderComponent } from '@shared/components/page-header/page-header.component';

@Component({
  selector: 'app-export',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatDatepickerModule,
    MatInputModule,
    MatProgressSpinnerModule,
    FormsModule,
    PageHeaderComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="settings.labels().export" />

      <mat-card class="export-card">
        <mat-card-header>
          <div class="export-header-row">
            <mat-icon class="export-icon">download</mat-icon>
            <div>
              <mat-card-title>{{ settings.labels().exportToExcel }}</mat-card-title>
              <mat-card-subtitle>{{ settings.labels().exportSubtitle }}</mat-card-subtitle>
            </div>
          </div>
        </mat-card-header>
        <mat-card-content>
          <div class="filter-row">
            <mat-form-field appearance="outline">
              <mat-label>{{ settings.labels().dateFrom }}</mat-label>
              <input matInput [matDatepicker]="fromPicker" [(ngModel)]="dateFrom">
              <mat-datepicker-toggle matIconSuffix [for]="fromPicker" />
              <mat-datepicker #fromPicker />
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>{{ settings.labels().dateTo }}</mat-label>
              <input matInput [matDatepicker]="toPicker" [(ngModel)]="dateTo">
              <mat-datepicker-toggle matIconSuffix [for]="toPicker" />
              <mat-datepicker #toPicker />
            </mat-form-field>
          </div>

          <div class="filter-row">
            <mat-form-field appearance="outline">
              <mat-label>{{ settings.labels().account }}</mat-label>
              <mat-select [(ngModel)]="accountId">
                <mat-option value="">{{ settings.labels().allItems }}</mat-option>
                @for (acc of accounts(); track acc.id) {
                  <mat-option [value]="acc.id">{{ acc.accountLabel }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>{{ settings.labels().category }}</mat-label>
              <mat-select [(ngModel)]="categoryId">
                <mat-option value="">{{ settings.labels().allItems }}</mat-option>
                @for (cat of categories(); track cat.id) {
                  <mat-option [value]="cat.id">{{ cat.name }}</mat-option>
                }
              </mat-select>
            </mat-form-field>
          </div>
        </mat-card-content>

        <mat-card-actions>
          <button mat-flat-button color="primary"
                  [disabled]="!dateFrom || !dateTo || downloading()"
                  (click)="download()">
            <mat-icon>download</mat-icon>
            {{ downloading() ? settings.labels().downloading : settings.labels().downloadExcel }}
          </button>
        </mat-card-actions>
      </mat-card>
    </div>
  `,
  styles: `
    .export-card {
      max-width: 600px;
      border-radius: var(--rad-lg);
      background: var(--clr-surface);
      border: 1px solid var(--clr-border);
      box-shadow: var(--elev-card);
    }

    .export-header-row {
      display: flex;
      align-items: center;
      gap: var(--spc-12);
    }

    .export-icon {
      font-size: var(--spc-40);
      width: var(--spc-40);
      height: var(--spc-40);
      color: var(--brand-primary);
      opacity: 0.7;
    }

    .filter-row {
      display: flex;
      gap: var(--spc-16);
      margin-top: var(--spc-16);
    }

    .filter-row mat-form-field {
      flex: 1;
    }

    mat-card-actions {
      padding: var(--spc-16);
    }
  `,
})
export class ExportComponent implements OnInit {
  private readonly refData = inject(ReferenceDataService);
  private readonly exportService = inject(ExportService);
  readonly settings = inject(AppSettingsService);

  readonly accounts = this.refData.accounts;
  readonly categories = this.refData.categories;
  readonly downloading = signal(false);

  dateFrom: Date | null = null;
  dateTo: Date | null = null;
  accountId = '';
  categoryId = '';

  ngOnInit(): void {
    // Default: current month
    const now = new Date();
    this.dateFrom = new Date(now.getFullYear(), now.getMonth(), 1);
    this.dateTo = now;
  }

  download(): void {
    if (!this.dateFrom || !this.dateTo) return;
    this.downloading.set(true);

    const params: ExportParams = {
      dateFrom: this.formatDate(this.dateFrom),
      dateTo: this.formatDate(this.dateTo),
      accountId: this.accountId || undefined,
      categoryId: this.categoryId || undefined,
    };

    this.exportService.downloadExcel(params).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `movimientos-${params.dateFrom}-${params.dateTo}.xlsx`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.downloading.set(false);
      },
      error: () => this.downloading.set(false),
    });
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}
