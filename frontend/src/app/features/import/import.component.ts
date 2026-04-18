import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatRadioModule } from '@angular/material/radio';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AppSettingsService } from '@core/services/app-settings.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { ImportService } from '@core/services/import.service';
import { CandidateSheet, ExcelImportSummary, IgnoredSheet, ImportPreview } from '@shared/models/import.model';
import { PageHeaderComponent } from '@shared/components/page-header/page-header.component';

@Component({
  selector: 'app-import',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatChipsModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatIconModule,
    MatListModule,
    MatProgressSpinnerModule,
    MatRadioModule,
    MatSelectModule,
    MatSnackBarModule,
    PageHeaderComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="settings.labels().import" />

      <div class="import-grid">
        <mat-card class="import-card hero-card">
          <mat-card-header>
            <mat-card-title>{{ settings.labels().importBankTemplate }}</mat-card-title>
            <mat-card-subtitle>{{ settings.labels().importSubtitle }}</mat-card-subtitle>
          </mat-card-header>

          <mat-card-content>
            <div class="step-label">{{ settings.labels().importStepAccount }}</div>
            <mat-form-field appearance="outline" class="account-select">
              <mat-label>{{ settings.labels().importSelectAccountPlaceholder }}</mat-label>
              <mat-select [value]="selectedAccountId()" (selectionChange)="onAccountSelected($event.value)">
                @for (acc of activeAccounts(); track acc.id) {
                  <mat-option [value]="acc.id">{{ acc.accountLabel }}{{ acc.iban ? ' (' + maskIban(acc.iban) + ')' : '' }}</mat-option>
                }
              </mat-select>
            </mat-form-field>

            <div class="step-label">{{ settings.labels().importStepFile }}</div>
            <div class="drop-zone" [class.has-file]="!!selectedFile()" [class.disabled]="!selectedAccountId()">
              <mat-icon>upload_file</mat-icon>
              <div>
                <strong>{{ selectedFile()?.name || settings.labels().selectXlsx }}</strong>
                <p>{{ settings.labels().unicajaDescription }}</p>
              </div>
            </div>

            <input #fileInput type="file" accept=".xlsx" hidden (change)="onFileSelected($event)" />

            <div class="action-row">
              <button mat-stroked-button color="primary" (click)="fileInput.click()" [disabled]="!selectedAccountId()">
                <mat-icon>folder_open</mat-icon>
                {{ settings.labels().chooseExcel }}
              </button>

              @if (!sheetSelection()) {
                <button
                  mat-flat-button
                  color="primary"
                  [disabled]="!selectedFile() || !selectedAccountId() || previewing() || importing()"
                  (click)="runPreview()"
                >
                  <mat-icon>fact_check</mat-icon>
                  {{ previewing() ? settings.labels().validating : settings.labels().previewBtn }}
                </button>
              }
            </div>
          </mat-card-content>
        </mat-card>

        <mat-card class="import-card info-card">
          <mat-card-header>
            <mat-card-title>{{ settings.labels().whatImportDoes }}</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <mat-list>
              <mat-list-item>{{ settings.labels().importStep1 }}</mat-list-item>
              <mat-list-item>{{ settings.labels().importStep2 }}</mat-list-item>
              <mat-list-item>{{ settings.labels().importStep3 }}</mat-list-item>
              <mat-list-item>{{ settings.labels().importStep4 }}</mat-list-item>
            </mat-list>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- Sheet selector (multi-sheet workbook) -->
      @if (sheetSelection(); as sel) {
        <mat-card class="status-card sheet-selector-card">
          <mat-card-header>
            <mat-card-title>
              <mat-icon class="inline-icon">layers</mat-icon>
              {{ settings.labels().importSheetSelectorTitle }}
            </mat-card-title>
            <mat-card-subtitle>{{ settings.labels().importSheetSelectorHelp }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <mat-radio-group
              class="sheet-radio-group"
              [value]="selectedSheetForPicker()"
              (change)="onSheetPicked($event.value)"
            >
              @for (s of sel.candidates; track s.name) {
                <mat-radio-button [value]="s.name" class="sheet-radio">
                  <span class="sheet-name">{{ s.name }}</span>
                  <span class="sheet-rows">{{ settings.labels().importSheetSelectorRows(s.dataRowCount) }}</span>
                </mat-radio-button>
              }
            </mat-radio-group>

            @if (sel.ignored.length) {
              <mat-expansion-panel class="ignored-panel">
                <mat-expansion-panel-header>
                  <mat-panel-title>{{ settings.labels().importSheetSelectorIgnored(sel.ignored.length) }}</mat-panel-title>
                </mat-expansion-panel-header>
                <mat-list dense>
                  @for (ig of sel.ignored; track ig.name) {
                    <mat-list-item class="ignored-item">
                      <strong>{{ ig.name }}</strong> — {{ ignoredReasonLabel(ig) }}
                    </mat-list-item>
                  }
                </mat-list>
              </mat-expansion-panel>
            }

            <div class="action-row">
              <button
                mat-flat-button
                color="primary"
                [disabled]="!selectedSheetForPicker() || previewing()"
                (click)="runPreview()"
              >
                <mat-icon>fact_check</mat-icon>
                {{ previewing() ? settings.labels().validating : settings.labels().previewBtn }}
              </button>
            </div>
          </mat-card-content>
        </mat-card>
      }

      <!-- Validation errors. The "requiresSheetSelection" guard avoids stacking
           the error card under the sheet picker on the discovery response
           (where valid is also false but the user simply hasn't picked a
           sheet yet — not an error). -->
      @if (preview()?.valid === false && !preview()?.requiresSheetSelection) {
        <mat-card class="status-card error-card">
          <mat-card-header>
            <mat-card-title>
              <mat-icon class="inline-icon error-icon">error</mat-icon>
              {{ settings.labels().validationFailed }}
            </mat-card-title>
            <mat-card-subtitle>{{ settings.labels().fixErrorsBeforeImport }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <mat-list>
              @for (err of preview()!.errors; track err) {
                <mat-list-item class="error-item">{{ err }}</mat-list-item>
              }
            </mat-list>
            @if (preview()!.ignoredSheets.length) {
              <div class="detail-block ignored-block">
                <h3>{{ settings.labels().importSheetSelectorIgnored(preview()!.ignoredSheets.length) }}</h3>
                <mat-list dense>
                  @for (ig of preview()!.ignoredSheets; track ig.name) {
                    <mat-list-item class="ignored-item">
                      <strong>{{ ig.name }}</strong> — {{ ignoredReasonLabel(ig) }}
                    </mat-list-item>
                  }
                </mat-list>
              </div>
            }
          </mat-card-content>
        </mat-card>
      }

      <!-- Preview summary (valid) -->
      @if (preview()?.valid === true) {
        <mat-card class="status-card preview-card">
          <mat-card-header>
            <mat-card-title>
              <mat-icon class="inline-icon ok-icon">check_circle</mat-icon>
              {{ settings.labels().previewTitle }}
              <mat-chip-set class="mode-chip-set">
                <mat-chip [class]="'mode-chip mode-' + preview()!.importMode" highlighted>
                  {{ importModeLabel() }}
                </mat-chip>
                @if (preview()!.selectedSheet) {
                  <mat-chip class="sheet-chip" highlighted>
                    <mat-icon matChipAvatar>description</mat-icon>
                    {{ settings.labels().importSheetBadge(preview()!.selectedSheet!) }}
                  </mat-chip>
                }
              </mat-chip-set>
            </mat-card-title>
            <mat-card-subtitle>
              {{ account_label() }}
            </mat-card-subtitle>
          </mat-card-header>

          <mat-card-content>
            <!-- Bank mode notice -->
            @if (preview()!.importMode === 'bank') {
              <div class="info-callout">
                <mat-icon>info</mat-icon>
                <span>{{ settings.labels().bankModeNotice }}</span>
              </div>
            }

            <!-- Inline mode notice -->
            @if (preview()!.importMode === 'inline') {
              <div class="info-callout inline-callout">
                <mat-icon>auto_awesome</mat-icon>
                <span>{{ settings.labels().inlineModeNotice }}</span>
              </div>
            }

            <div class="summary-grid">
              @if (preview()!.importMode !== 'bank') {
                <div class="summary-tile">
                  <span class="tile-label">{{ settings.labels().newCategoriesCount }}</span>
                  <strong>{{ preview()!.newCategories.length }}</strong>
                </div>
                <div class="summary-tile">
                  <span class="tile-label">{{ settings.labels().newSubcategoriesCount }}</span>
                  <strong>{{ preview()!.newSubcategories.length }}</strong>
                </div>
              }
              <div class="summary-tile">
                <span class="tile-label">{{ settings.labels().transactionsToImport }}</span>
                <strong>{{ preview()!.transactionsToImport }}</strong>
              </div>
              <div class="summary-tile">
                <span class="tile-label">{{ settings.labels().duplicatesToSkip }}</span>
                <strong>{{ preview()!.duplicatesToSkip }}</strong>
              </div>
              <div class="summary-tile">
                <span class="tile-label">{{ settings.labels().totalRows }}</span>
                <strong>{{ preview()!.totalRows }}</strong>
              </div>
            </div>

            @if (preview()!.duplicateRows.length) {
              <mat-expansion-panel class="duplicates-panel">
                <mat-expansion-panel-header>
                  <mat-panel-title>
                    <mat-icon class="inline-icon">content_copy</mat-icon>
                    {{ settings.labels().importDuplicateDetails(preview()!.duplicateRows.length) }}
                  </mat-panel-title>
                </mat-expansion-panel-header>
                <table class="duplicates-table">
                  <thead>
                    <tr>
                      <th>{{ settings.labels().importDuplicateRow }}</th>
                      <th>{{ settings.labels().date }}</th>
                      <th>{{ settings.labels().amount }}</th>
                      <th>{{ settings.labels().description }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (dup of preview()!.duplicateRows; track dup.row) {
                      <tr>
                        <td>{{ dup.row }}</td>
                        <td>{{ dup.date ?? '—' }}</td>
                        <td>{{ dup.amount != null ? dup.amount : '—' }}</td>
                        <td class="dup-desc">{{ dup.description ?? '—' }}</td>
                      </tr>
                    }
                  </tbody>
                </table>
              </mat-expansion-panel>
            }

            @if (preview()!.importMode !== 'bank' && preview()!.newCategories.length) {
              <!-- Full mode: categories from sheet -->
              @if (preview()!.importMode === 'full') {
                <div class="detail-block">
                  <h3>{{ settings.labels().categoriesToCreate }}</h3>
                  <mat-list dense>
                    @for (cat of preview()!.newCategories; track cat.name) {
                      <mat-list-item>{{ cat.name }} ({{ cat.suggestedType }})</mat-list-item>
                    }
                  </mat-list>
                </div>
              }

              <!-- Inline mode: categories with type toggles -->
              @if (preview()!.importMode === 'inline') {
                <div class="detail-block">
                  <h3>{{ settings.labels().importNewCategories }}</h3>
                  <p class="type-hint">{{ settings.labels().importCategoryTypeHint }}</p>
                  @for (cat of preview()!.newCategories; track cat.name) {
                    <div class="category-type-row">
                      <span class="category-name">{{ cat.name }}</span>
                      <mat-button-toggle-group
                        [value]="getCategoryType(cat.name, cat.suggestedType)"
                        (change)="onCategoryTypeChange(cat.name, $event.value)"
                      >
                        <mat-button-toggle value="income">{{ settings.labels().importCategoryTypeIncome }}</mat-button-toggle>
                        <mat-button-toggle value="expense">{{ settings.labels().importCategoryTypeExpense }}</mat-button-toggle>
                      </mat-button-toggle-group>
                    </div>
                  }
                </div>
              }
            }

            @if (preview()!.importMode !== 'bank' && preview()!.newSubcategories.length) {
              <div class="detail-block">
                <h3>{{ settings.labels().subcategoriesToCreate }}</h3>
                <mat-list dense>
                  @for (sub of preview()!.newSubcategories; track sub.name) {
                    <mat-list-item>{{ sub.categoryName }} → {{ sub.name }}</mat-list-item>
                  }
                </mat-list>
              </div>
            }

            @if (preview()!.warnings.length) {
              <div class="detail-block warnings-block">
                <h3>{{ settings.labels().importWarnings }}</h3>
                <mat-list dense>
                  @for (w of preview()!.warnings; track w) {
                    <mat-list-item class="warning-item">{{ w }}</mat-list-item>
                  }
                </mat-list>
              </div>
            }

            <div class="action-row">
              <button mat-stroked-button (click)="cancelPreview()">
                {{ settings.labels().cancel }}
              </button>
              <button
                mat-flat-button
                color="primary"
                [disabled]="importing() || pickerDriftedFromValidated()"
                (click)="confirmImport()"
              >
                <mat-icon>cloud_upload</mat-icon>
                {{ importing() ? settings.labels().importing : confirmBtnLabel() }}
              </button>
            </div>
          </mat-card-content>
        </mat-card>
      }

      <!-- API error -->
      @if (error()) {
        <mat-card class="status-card error-card">
          <mat-card-content>
            <div class="status-row">
              <mat-icon>error</mat-icon>
              <span>{{ error() }}</span>
            </div>
          </mat-card-content>
        </mat-card>
      }

      <!-- Import result -->
      @if (summary(); as result) {
        <mat-card class="status-card summary-card">
          <mat-card-header>
            <mat-card-title>
              {{ settings.labels().importResultTitle }}
              <mat-chip-set class="mode-chip-set">
                <mat-chip [class]="'mode-chip mode-' + result.importMode" highlighted>
                  {{ summaryModeLabel() }}
                </mat-chip>
              </mat-chip-set>
            </mat-card-title>
            <mat-card-subtitle>
              {{ settings.labels().account }}: {{ result.accountLabel }}
              <span class="batch-id">{{ settings.labels().importBatchId }}: {{ result.importBatchId }}</span>
            </mat-card-subtitle>
          </mat-card-header>

          <mat-card-content>
            <div class="summary-grid">
              @if (result.importMode !== 'bank') {
                <div class="summary-tile">
                  <span class="tile-label">{{ settings.labels().categoriesCreated }}</span>
                  <strong>{{ result.categoriesCreated }}</strong>
                </div>
                <div class="summary-tile">
                  <span class="tile-label">{{ settings.labels().subcategoriesAdded }}</span>
                  <strong>{{ result.subcategoriesAdded }}</strong>
                </div>
              }
              <div class="summary-tile">
                <span class="tile-label">{{ settings.labels().transactionsImported }}</span>
                <strong>{{ result.transactionsImported }}</strong>
              </div>
              <div class="summary-tile">
                <span class="tile-label">{{ settings.labels().duplicatesSkipped }}</span>
                <strong>{{ result.duplicatesSkipped }}</strong>
              </div>
              <div class="summary-tile">
                <span class="tile-label">{{ settings.labels().rowsSkipped }}</span>
                <strong>{{ result.rowsSkipped }}</strong>
              </div>
              <div class="summary-tile">
                <span class="tile-label">{{ settings.labels().totalCategoriesLoaded }}</span>
                <strong>{{ categoryCount() }}</strong>
              </div>
            </div>

            @if (result.importMode === 'bank') {
              <div class="info-callout summary-notice">
                <mat-icon>task_alt</mat-icon>
                <span>{{ settings.labels().bankModeSummaryNotice }}</span>
              </div>
            }

            @if (result.warnings.length) {
              <div class="warnings-block">
                <h3>{{ settings.labels().importWarnings }}</h3>
                <mat-list>
                  @for (warning of result.warnings; track warning) {
                    <mat-list-item>{{ warning }}</mat-list-item>
                  }
                </mat-list>
              </div>
            }
          </mat-card-content>
        </mat-card>
      }
    </div>
  `,
  styles: `
    .import-grid {
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
      gap: var(--spc-16);
      margin-bottom: var(--spc-16);
    }

    .import-card,
    .status-card {
      border-radius: var(--rad-lg);
    }

    .drop-zone {
      display: flex;
      align-items: center;
      gap: var(--spc-16);
      padding: var(--spc-20);
      border: 2px dashed var(--brand-primary-muted);
      border-radius: var(--rad-lg);
      background: var(--brand-surface);
      margin-top: var(--spc-16);
    }

    .drop-zone.has-file {
      border-style: solid;
      background: var(--brand-surface-hover);
    }

    .drop-zone mat-icon {
      font-size: 36px;
      width: 36px;
      height: 36px;
      color: var(--brand-primary);
    }

    .drop-zone p {
      margin: var(--spc-4) 0 0;
      color: var(--clr-text-muted);
    }

    .action-row {
      display: flex;
      gap: var(--spc-12);
      margin-top: var(--spc-20);
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: var(--spc-12);
    }

    .summary-tile {
      padding: var(--spc-12) var(--spc-16);
      border-radius: var(--rad-md);
      background: var(--brand-surface);
      display: flex;
      flex-direction: column;
      gap: var(--spc-6);
    }

    .tile-label {
      color: var(--clr-text-muted);
      font-size: var(--font-sm);
      text-transform: uppercase;
      letter-spacing: var(--ls-section);
    }

    .summary-tile strong {
      font-size: var(--font-2xl);
      line-height: var(--lh-tight);
    }

    .status-row {
      display: flex;
      align-items: center;
      gap: var(--spc-10);
      color: var(--clr-expense);
    }

    .inline-icon {
      vertical-align: middle;
      margin-right: var(--spc-6);
    }

    .error-icon { color: var(--clr-expense); }
    .ok-icon { color: var(--clr-income); }

    .error-card {
      border-left: 4px solid var(--clr-expense);
      margin-bottom: var(--spc-16);
    }

    .error-item { color: var(--clr-expense); }
    .warning-item { color: var(--clr-warning); }

    .preview-card {
      border-left: 4px solid var(--clr-income);
      margin-bottom: var(--spc-16);
    }

    .summary-card {
      border-left: 4px solid var(--brand-primary);
      margin-bottom: var(--spc-16);
    }

    .detail-block {
      margin-top: var(--spc-16);
    }

    .detail-block h3 {
      margin: 0 0 var(--spc-4);
      font-size: var(--font-body);
      color: var(--clr-text-muted);
      text-transform: uppercase;
      letter-spacing: var(--ls-section);
    }

    .warnings-block {
      margin-top: var(--spc-20);
    }

    .warnings-block h3 {
      margin: 0 0 var(--spc-8);
      font-size: var(--font-md);
    }

    .mode-chip-set {
      display: inline-flex;
      vertical-align: middle;
      margin-left: var(--spc-8);
    }

    .mode-chip {
      font-size: var(--font-sm);
      font-weight: var(--fw-medium);
    }

    .mode-full { --mdc-chip-elevated-container-color: var(--clr-income-bg); --mdc-chip-label-text-color: var(--clr-income-on-bg); }
    .mode-inline { --mdc-chip-elevated-container-color: var(--clr-transfer-bg); --mdc-chip-label-text-color: var(--clr-transfer-on-bg); }
    .mode-bank { --mdc-chip-elevated-container-color: var(--clr-warning-bg); --mdc-chip-label-text-color: var(--clr-warning-on-bg); }

    .info-callout {
      display: flex;
      align-items: center;
      gap: var(--spc-10);
      padding: var(--spc-12) var(--spc-16);
      border-radius: var(--rad-md);
      background: var(--clr-info-bg);
      color: var(--clr-info);
      margin-bottom: var(--spc-16);
    }

    .inline-callout {
      background: var(--clr-info-bg);
    }

    .summary-notice {
      margin-top: var(--spc-16);
    }

    .inferred-chip {
      font-size: var(--font-xs);
      margin-left: var(--spc-8);
      --mdc-chip-elevated-container-color: var(--clr-transfer-bg);
      --mdc-chip-label-text-color: var(--clr-transfer-on-bg);
    }

    .account-select {
      width: 100%;
    }

    .step-label {
      font-size: var(--font-sm);
      text-transform: uppercase;
      letter-spacing: var(--ls-section);
      color: var(--clr-text-muted);
      margin-bottom: var(--spc-8);
      font-weight: var(--fw-medium);
    }

    .drop-zone.disabled {
      opacity: 0.45;
      pointer-events: none;
    }

    .category-type-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--spc-12);
      padding: var(--spc-8) 0;
      border-bottom: 1px solid var(--clr-divider);
    }

    .category-name {
      font-weight: var(--fw-medium);
    }

    .type-hint {
      font-size: var(--font-body);
      color: var(--clr-text-muted);
      margin: var(--spc-4) 0 var(--spc-12);
    }

    .batch-id {
      display: block;
      font-size: var(--font-xs);
      color: var(--clr-text-muted);
      margin-top: var(--spc-2);
    }

    .sheet-selector-card {
      border-left: 4px solid var(--brand-primary);
      margin-bottom: var(--spc-16);
    }

    .duplicates-panel {
      margin-top: var(--spc-8);
      margin-bottom: var(--spc-8);
      box-shadow: none;
      background: var(--brand-surface);
    }

    .duplicates-table {
      width: 100%;
      border-collapse: collapse;
      font-size: var(--font-sm);
    }

    .duplicates-table th {
      text-align: left;
      font-weight: var(--fw-semibold);
      padding: var(--spc-4) var(--spc-8);
      border-bottom: 1px solid var(--clr-border, #e0e0e0);
      color: var(--clr-text-muted);
    }

    .duplicates-table td {
      padding: var(--spc-4) var(--spc-8);
      border-bottom: 1px solid var(--clr-border-light, #f0f0f0);
    }

    .dup-desc {
      max-width: 300px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .sheet-radio-group {
      display: flex;
      flex-direction: column;
      gap: 0;
      max-height: 240px;
      overflow-y: auto;
      margin-bottom: var(--spc-8);
      border: 1px solid var(--clr-border, #e0e0e0);
      border-radius: 4px;
      padding: var(--spc-4) 0;
    }

    .sheet-radio {
      padding: var(--spc-2) var(--spc-8);
    }

    .sheet-name {
      font-weight: var(--fw-medium);
      margin-right: var(--spc-8);
    }

    .sheet-rows {
      color: var(--clr-text-muted);
      font-size: var(--font-sm);
    }

    .ignored-panel {
      margin-top: var(--spc-8);
      box-shadow: none;
      background: var(--brand-surface);
    }

    .ignored-item {
      color: var(--clr-text-muted);
      font-size: var(--font-sm);
    }

    .ignored-block {
      margin-top: var(--spc-12);
    }

    .sheet-chip {
      --mdc-chip-elevated-container-color: var(--brand-surface);
      --mdc-chip-label-text-color: var(--clr-text);
    }

    @media (max-width: 960px) {
      .import-grid {
        grid-template-columns: 1fr;
      }

      .action-row {
        flex-direction: column;
      }
    }
  `,
})
export class ImportComponent {
  private readonly importService = inject(ImportService);
  private readonly refData = inject(ReferenceDataService);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);

  readonly previewing = signal(false);
  readonly importing = signal(false);
  readonly selectedFile = signal<File | null>(null);
  readonly selectedAccountId = signal<string | null>(null);
  readonly preview = signal<ImportPreview | null>(null);
  readonly summary = signal<ExcelImportSummary | null>(null);
  readonly error = signal<string | null>(null);
  readonly categoryTypeSelections = signal<Record<string, string>>({});
  /**
   * Sheet currently chosen in the picker. May differ from the validated sheet
   * (`preview().selectedSheet`) until the user re-runs preview.
   */
  readonly selectedSheetForPicker = signal<string | null>(null);
  /**
   * Discovered candidate/ignored sheets for the current workbook. Captured
   * from the first preview response that returns a discovery payload and kept
   * across subsequent previews so the selector stays visible after a
   * successful validation (spec: "selector remains visible after a successful
   * preview"). Cleared whenever the file/account selection is reset.
   */
  readonly discovery = signal<{ candidates: CandidateSheet[]; ignored: IgnoredSheet[] } | null>(null);

  readonly activeAccounts = computed(() => this.refData.accounts().filter(a => a.isActive));
  readonly categoryCount = computed(() => this.refData.categories().length);
  readonly account_label = computed(() => {
    const p = this.preview();
    return p?.account.label ?? '';
  });

  /**
   * Discovery payload to render the sheet selector. Sourced from the
   * `discovery` signal so the picker stays visible across re-previews of
   * different sheets — not just on the initial discovery response.
   */
  readonly sheetSelection = computed(() => this.discovery());

  /**
   * True when the user has changed the picker selection after a successful
   * preview without re-validating. Used to disable Confirm so we never commit
   * data the user did not validate.
   */
  readonly pickerDriftedFromValidated = computed(() => {
    const p = this.preview();
    if (!p?.valid) return false;
    const validated = p.selectedSheet;
    const picked = this.selectedSheetForPicker();
    return validated !== null && picked !== null && validated !== picked;
  });

  readonly importModeLabel = computed(() => {
    const mode = this.preview()?.importMode;
    const labels = this.settings.labels();
    if (mode === 'inline') return labels.importModeInline;
    if (mode === 'bank') return labels.importModeBank;
    return labels.importModeFull;
  });

  readonly summaryModeLabel = computed(() => {
    const mode = this.summary()?.importMode;
    const labels = this.settings.labels();
    if (mode === 'inline') return labels.importModeInline;
    if (mode === 'bank') return labels.importModeBank;
    return labels.importModeFull;
  });

  readonly confirmBtnLabel = computed(() => {
    const mode = this.preview()?.importMode;
    const labels = this.settings.labels();
    return mode === 'bank' ? labels.importStatementBtn : labels.confirmImportBtn;
  });

  constructor() {
    this.refData.load();
  }

  onAccountSelected(accountId: string): void {
    this.selectedAccountId.set(accountId);
    this.resetState();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedFile.set(file);
    this.resetState();
  }

  onSheetPicked(sheet: string): void {
    this.selectedSheetForPicker.set(sheet);
    // When the user changes the selection after a valid preview, clear the
    // preview so Confirm cannot fire against stale data.
    const p = this.preview();
    if (p?.valid && p.selectedSheet !== sheet) {
      this.preview.set(null);
      this.summary.set(null);
      this.categoryTypeSelections.set({});
    }
  }

  ignoredReasonLabel(ig: IgnoredSheet): string {
    if (ig.reason === 'empty') return this.settings.labels().importSheetReasonEmpty;
    if (ig.reason === 'missing_required_headers') {
      const list = (ig.missing ?? []).join(', ');
      return this.settings.labels().importSheetReasonNoHeaders(list);
    }
    return ig.reason;
  }

  getCategoryType(name: string, defaultType: string): string {
    return this.categoryTypeSelections()[name] ?? defaultType;
  }

  onCategoryTypeChange(categoryName: string, newType: string): void {
    this.categoryTypeSelections.update(prev => ({ ...prev, [categoryName]: newType }));
  }

  runPreview(): void {
    const file = this.selectedFile();
    const accountId = this.selectedAccountId();
    if (!file || !accountId) return;

    this.previewing.set(true);
    // Preserve the picker selection and the cached discovery payload across
    // preview reloads: the radio stays on the user's choice, and the selector
    // remains rendered while we clear the previous validation result.
    const pickerSheet = this.selectedSheetForPicker();
    this.preview.set(null);
    this.summary.set(null);
    this.error.set(null);
    this.categoryTypeSelections.set({});

    this.importService.preview(file, accountId, pickerSheet ?? undefined).subscribe({
      next: (result) => {
        this.preview.set(result);
        // Capture the discovery payload the first time the backend offers one
        // so the sheet selector remains visible across subsequent re-previews
        // of different sheets (per spec). Don't overwrite it on later previews
        // — those responses carry an empty `candidateSheets` because the user
        // already passed an explicit `sheet` param.
        if (result.requiresSheetSelection && result.candidateSheets.length) {
          this.discovery.set({
            candidates: result.candidateSheets,
            ignored: result.ignoredSheets,
          });
        }
        // Default the picker to the first candidate when discovery returns one,
        // or to the validated sheet when the response is a normal preview.
        if (result.requiresSheetSelection && result.candidateSheets.length) {
          this.selectedSheetForPicker.set(
            this.selectedSheetForPicker() ?? result.candidateSheets[0].name,
          );
        } else if (result.selectedSheet) {
          this.selectedSheetForPicker.set(result.selectedSheet);
        }
        this.initCategoryTypeSelections(result);
        this.previewing.set(false);
      },
      error: (err) => {
        const detail = err?.error?.detail;
        if (typeof detail === 'string') {
          this.error.set(detail);
        } else if (Array.isArray(detail)) {
          this.error.set(detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; '));
        } else {
          this.error.set(this.settings.labels().importValidateError);
        }
        this.previewing.set(false);
      },
    });
  }

  confirmImport(): void {
    const file = this.selectedFile();
    const accountId = this.selectedAccountId();
    if (!file || !accountId) return;
    // Only commit the sheet that was actually validated.
    const validatedSheet = this.preview()?.selectedSheet ?? undefined;

    this.importing.set(true);
    this.error.set(null);

    const overrides = this.buildCategoryTypeOverrides();
    this.importService.importWorkbook(file, accountId, overrides, validatedSheet).subscribe({
      next: (result) => {
        this.summary.set(result);
        this.preview.set(null);
        this.refData.invalidate();
        this.importing.set(false);
        this.snackBar.open(
          this.settings.labels().importedCount(result.transactionsImported),
          this.settings.labels().close,
          { duration: 6000 },
        );
      },
      error: (err) => {
        this.error.set(err?.error?.detail || this.settings.labels().importError);
        this.importing.set(false);
      },
    });
  }

  cancelPreview(): void {
    this.preview.set(null);
    this.selectedSheetForPicker.set(null);
    this.discovery.set(null);
  }

  private initCategoryTypeSelections(result: ImportPreview): void {
    if (result.importMode !== 'inline' || !result.newCategories.length) {
      this.categoryTypeSelections.set({});
      return;
    }
    const selections: Record<string, string> = {};
    for (const cat of result.newCategories) {
      selections[cat.name] = cat.suggestedType;
    }
    this.categoryTypeSelections.set(selections);
  }

  private buildCategoryTypeOverrides(): Record<string, string> | undefined {
    const p = this.preview();
    if (!p || p.importMode !== 'inline' || !p.newCategories.length) return undefined;

    const overrides: Record<string, string> = {};
    const selections = this.categoryTypeSelections();
    for (const cat of p.newCategories) {
      const selected = selections[cat.name] ?? cat.suggestedType;
      if (selected !== cat.suggestedType) {
        overrides[cat.name] = selected;
      }
    }
    return Object.keys(overrides).length > 0 ? overrides : undefined;
  }

  private resetState(): void {
    this.preview.set(null);
    this.summary.set(null);
    this.error.set(null);
    this.categoryTypeSelections.set({});
    this.selectedSheetForPicker.set(null);
    this.discovery.set(null);
  }

  maskIban(iban: string): string {
    const clean = iban.replace(/\s/g, '');
    if (clean.length <= 8) return clean;
    const first = clean.slice(0, 4);
    const last = clean.slice(-4);
    const masked = '*'.repeat(clean.length - 8);
    const full = first + masked + last;
    return full.replace(/(.{4})/g, '$1 ').trim();
  }
}
