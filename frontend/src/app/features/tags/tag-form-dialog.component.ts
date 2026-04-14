import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import {
  FormBuilder,
  FormGroup,
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
import { ReferenceDataService } from '@core/services/reference-data.service';
import { TagService } from '@core/services/tag.service';
import { Tag } from '@shared/models/tag.model';

const PRESET_COLORS = [
  '#b39ddb', // lavender (brand)
  '#6d4d8c', // brand primary
  '#ef5350', // red
  '#ec407a', // pink
  '#42a5f5', // blue
  '#26a69a', // teal
  '#66bb6a', // green
  '#ffa726', // orange
  '#8d6e63', // brown
  '#78909c', // blue-grey
];

@Component({
  selector: 'app-tag-form-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
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
        <mat-icon class="title-icon">label</mat-icon>
        <h2 mat-dialog-title>{{ data ? settings.labels().editTag : settings.labels().newTag }}</h2>
      </div>
      <button mat-icon-button mat-dialog-close class="close-btn" aria-label="Close">
        <mat-icon>close</mat-icon>
      </button>
    </div>

    <mat-dialog-content>
      <form [formGroup]="form">
        <!-- Name -->
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>{{ settings.labels().name }}</mat-label>
          <input matInput formControlName="name">
        </mat-form-field>

        <!-- Color palette -->
        <div class="color-section">
          <span class="color-label" aria-hidden="true">{{ settings.labels().presetColors }}</span>
          <div class="color-grid" role="radiogroup" [attr.aria-label]="settings.labels().presetColors">
            @for (color of presetColors; track color) {
              <button type="button" class="color-swatch"
                      [style.background-color]="color"
                      [class.selected]="form.value.color === color"
                      (click)="form.patchValue({ color })"
                      [attr.aria-label]="color">
                @if (form.value.color === color) {
                  <mat-icon [style.color]="refData.contrastColor(color)">check</mat-icon>
                }
              </button>
            }
            <button type="button" class="color-swatch other-swatch"
                    [class.selected]="!isPresetColor()"
                    (click)="colorPicker.click()">
              <mat-icon>palette</mat-icon>
            </button>
            <input #colorPicker type="color" class="hidden-picker"
                   [value]="form.value.color"
                   (input)="form.patchValue({ color: colorPicker.value })">
          </div>
          @if (!isPresetColor()) {
            <span class="custom-color-label">{{ settings.labels().otherColor }}: {{ form.value.color }}</span>
          }
        </div>

        <!-- Live preview -->
        <div class="preview-section">
          <span class="preview-label" aria-hidden="true">{{ settings.labels().tagPreview }}</span>
          <div class="tag-preview-pill"
               [style.background-color]="form.value.color"
               [style.color]="refData.contrastColor(form.value.color)">
            {{ form.value.name || settings.labels().name }}
          </div>
        </div>

        <!-- Sort order -->
        <mat-form-field appearance="outline" class="order-field">
          <mat-label>{{ settings.labels().order }}</mat-label>
          <input matInput type="number" formControlName="sortOrder">
        </mat-form-field>

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

    /* --- Color palette --- */
    .color-section {
      margin-bottom: var(--spc-16);
    }
    .color-label, .preview-label {
      display: block;
      margin-bottom: var(--spc-8);
      font-size: var(--font-sm);
      font-weight: var(--fw-medium);
      color: var(--clr-text-secondary);
    }
    .color-grid {
      display: flex;
      flex-wrap: wrap;
      gap: var(--spc-8);
    }
    .color-swatch {
      width: 36px;
      height: 36px;
      border-radius: var(--rad-round);
      border: 2px solid transparent;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--transition-fast);
      padding: 0;
    }
    .color-swatch:hover {
      transform: scale(1.12);
    }
    .color-swatch.selected {
      border-color: var(--clr-text-primary);
      box-shadow: 0 0 0 2px var(--clr-surface), 0 0 0 4px var(--clr-text-primary);
    }
    .color-swatch mat-icon {
      font-size: var(--font-md);
      width: 16px;
      height: 16px;
    }
    .other-swatch {
      background: conic-gradient(
        red, yellow, lime, aqua, blue, magenta, red
      ) !important;
      color: white;
    }
    .hidden-picker {
      position: absolute;
      width: 0;
      height: 0;
      opacity: 0;
      pointer-events: none;
    }
    .custom-color-label {
      display: block;
      margin-top: var(--spc-6);
      font-size: var(--font-xs);
      color: var(--clr-text-muted);
      font-family: monospace;
    }

    /* --- Preview --- */
    .preview-section {
      margin-bottom: var(--spc-20);
    }
    .tag-preview-pill {
      display: inline-block;
      padding: var(--spc-6) var(--spc-16);
      border-radius: var(--rad-pill);
      font-size: var(--font-body);
      font-weight: var(--fw-medium);
      transition: all var(--transition-fast);
    }

    /* --- Order field --- */
    .order-field {
      width: 120px;
    }

    /* --- Active toggle --- */
    .active-toggle-row {
      margin-top: var(--spc-8);
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
export class TagFormDialogComponent {
  readonly data = inject<Tag | null>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<TagFormDialogComponent>);
  private readonly fb = inject(FormBuilder);
  private readonly tagService = inject(TagService);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);
  readonly refData = inject(ReferenceDataService);

  readonly saving = signal(false);
  readonly presetColors = PRESET_COLORS;

  form: FormGroup = this.fb.group({
    name: [this.data?.name ?? '', Validators.required],
    color: [this.data?.color ?? '#b39ddb', Validators.required],
    sortOrder: [this.data?.sortOrder ?? 0],
    isActive: [this.data?.isActive ?? true],
  });

  isPresetColor(): boolean {
    return PRESET_COLORS.includes(this.form.value.color);
  }

  onSave(): void {
    if (this.form.invalid) return;
    this.saving.set(true);

    const payload = this.form.value;
    const obs = this.data
      ? this.tagService.update(this.data.id, payload)
      : this.tagService.create(payload);

    obs.subscribe({
      next: () => this.dialogRef.close(true),
      error: (err) => {
        this.saving.set(false);
        const msg = err?.error?.detail || this.settings.labels().tagSaveError;
        this.snackBar.open(msg, this.settings.labels().close, { duration: 6000, panelClass: 'error-snack' });
      },
    });
  }
}
