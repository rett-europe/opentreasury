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
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AppSettingsService } from '@core/services/app-settings.service';
import { AccountService } from '@core/services/account.service';
import { BankAccount } from '@shared/models/account.model';

@Component({
  selector: 'app-account-form-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="dialog-header">
      <div class="dialog-title-row">
        <mat-icon class="title-icon">account_balance</mat-icon>
        <h2 mat-dialog-title>{{ data ? settings.labels().editAccount : settings.labels().newAccount }}</h2>
      </div>
      <button mat-icon-button mat-dialog-close class="close-btn" aria-label="Close">
        <mat-icon>close</mat-icon>
      </button>
    </div>

    <mat-dialog-content>
      <form [formGroup]="form">
        <!-- Account type toggle cards -->
        <div class="type-toggle-cards">
          <button type="button" class="type-card bank"
                  [class.selected]="!form.value.isPaypal"
                  (click)="form.patchValue({ isPaypal: false })">
            <mat-icon>account_balance</mat-icon>
            <span>{{ settings.labels().bankType }}</span>
          </button>
          <button type="button" class="type-card paypal"
                  [class.selected]="form.value.isPaypal"
                  (click)="form.patchValue({ isPaypal: true })">
            <mat-icon>payment</mat-icon>
            <span>{{ settings.labels().paypalType }}</span>
          </button>
        </div>

        <!-- Bank name -->
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>{{ settings.labels().bankName }}</mat-label>
          <input matInput formControlName="bankName">
        </mat-form-field>

        <!-- Short name + Account label row -->
        <div class="two-col">
          <mat-form-field appearance="outline">
            <mat-label>{{ settings.labels().shortName }}</mat-label>
            <input matInput formControlName="bankNameShort">
          </mat-form-field>
          <mat-form-field appearance="outline">
            <mat-label>{{ settings.labels().accountLabel }}</mat-label>
            <input matInput formControlName="accountLabel">
          </mat-form-field>
        </div>

        <!-- Conditional: IBAN for bank, email for PayPal -->
        @if (!form.value.isPaypal) {
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>{{ settings.labels().ibanLabel }}</mat-label>
            <input matInput formControlName="iban"
                   placeholder="ES00 0000 0000 0000 0000 0000"
                   (input)="formatIban($event)">
          </mat-form-field>
        } @else {
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>{{ settings.labels().paypalEmail }}</mat-label>
            <input matInput formControlName="paypalEmail" type="email">
          </mat-form-field>
        }

        <!-- Currency + Sort Order row -->
        <div class="two-col">
          <mat-form-field appearance="outline">
            <mat-label>{{ settings.labels().currency }}</mat-label>
            <mat-select formControlName="currency">
              <mat-option value="EUR">🇪🇺 EUR</mat-option>
              <mat-option value="USD">🇺🇸 USD</mat-option>
              <mat-option value="GBP">🇬🇧 GBP</mat-option>
            </mat-select>
          </mat-form-field>
          <mat-form-field appearance="outline">
            <mat-label>{{ settings.labels().order }}</mat-label>
            <input matInput type="number" formControlName="sortOrder">
          </mat-form-field>
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
    .type-card.bank.selected {
      border-color: var(--brand-primary);
      background: var(--brand-surface);
      color: var(--brand-primary);
    }
    .type-card.paypal.selected {
      border-color: var(--clr-transfer);
      background: var(--clr-transfer-bg);
      color: var(--clr-transfer);
    }

    /* --- Two-column layout --- */
    .two-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--spc-12);
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
export class AccountFormDialogComponent {
  readonly data = inject<BankAccount | null>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<AccountFormDialogComponent>);
  private readonly fb = inject(FormBuilder);
  private readonly accountService = inject(AccountService);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);

  readonly saving = signal(false);

  form: FormGroup = this.fb.group({
    bankName: [this.data?.bankName ?? '', Validators.required],
    bankNameShort: [this.data?.bankNameShort ?? ''],
    accountLabel: [this.data?.accountLabel ?? '', Validators.required],
    isPaypal: [this.data?.isPaypal ?? false],
    iban: [this.formatIbanValue(this.data?.iban ?? '')],
    paypalEmail: [this.data?.paypalEmail ?? ''],
    currency: [this.data?.currency ?? 'EUR'],
    sortOrder: [this.data?.sortOrder ?? 0],
    isActive: [this.data?.isActive ?? true],
  });

  formatIban(event: Event): void {
    const input = event.target as HTMLInputElement;
    const raw = input.value.replace(/\s/g, '').toUpperCase();
    const formatted = raw.replace(/(.{4})/g, '$1 ').trim();
    this.form.patchValue({ iban: formatted }, { emitEvent: false });
    input.value = formatted;
  }

  private formatIbanValue(iban: string): string {
    if (!iban) return '';
    const raw = iban.replace(/\s/g, '').toUpperCase();
    return raw.replace(/(.{4})/g, '$1 ').trim();
  }

  onSave(): void {
    if (this.form.invalid) return;
    this.saving.set(true);

    const payload = { ...this.form.value };
    // Strip IBAN spaces before sending to backend
    if (payload.iban) {
      payload.iban = payload.iban.replace(/\s/g, '');
    }

    const obs = this.data
      ? this.accountService.update(this.data.id, payload)
      : this.accountService.create(payload);

    obs.subscribe({
      next: () => this.dialogRef.close(true),
      error: (err) => {
        this.saving.set(false);
        const msg = err?.error?.detail || this.settings.labels().accountSaveError;
        this.snackBar.open(msg, this.settings.labels().close, { duration: 6000, panelClass: 'error-snack' });
      },
    });
  }
}
