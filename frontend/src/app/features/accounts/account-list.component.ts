import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AppSettingsService } from '@core/services/app-settings.service';
import { AccountService } from '@core/services/account.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { BankAccount } from '@shared/models/account.model';
import { AccountFormDialogComponent } from './account-form-dialog.component';
import { LoadingContainerComponent } from '@shared/components/loading-container/loading-container.component';
import { EmptyStateComponent } from '@shared/components/empty-state/empty-state.component';
import { PageHeaderComponent } from '@shared/components/page-header/page-header.component';
import { ConfirmDialogComponent, ConfirmDialogData } from '@shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-account-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatSlideToggleModule,
    MatDialogModule,
    MatSnackBarModule,
    LoadingContainerComponent,
    EmptyStateComponent,
    PageHeaderComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="settings.labels().bankAccounts">
        <button mat-fab extended color="primary" (click)="openForm()">
          <mat-icon>add</mat-icon>
          {{ settings.labels().newAccount }}
        </button>
      </app-page-header>

      <app-loading-container [loading]="loading()">
        <div class="card-grid">
          @for (acc of accounts(); track acc.id) {
            <mat-card class="account-card" [class.inactive]="!acc.isActive"
                      [style.border-left-color]="acc.color || null"
                      [class.has-color]="!!acc.color">
              <mat-card-header>
                <mat-icon mat-card-avatar class="card-icon"
                          [style.background-color]="acc.color || null"
                          [style.color]="acc.color ? '#1f2937' : null">
                  {{ acc.isPaypal ? 'payment' : 'account_balance' }}
                </mat-icon>
                <mat-card-title>
                  {{ acc.accountLabel }}
                  <span class="currency-badge">{{ acc.currency || 'EUR' }}</span>
                  @if (!acc.isActive) {
                    <span class="inactive-badge">{{ settings.labels().inactiveLabel }}</span>
                  }
                </mat-card-title>
                <mat-card-subtitle>{{ acc.bankName }}</mat-card-subtitle>
              </mat-card-header>
              <mat-card-content>
                @if (acc.iban) {
                  <p class="iban">{{ formatIbanMasked(acc.iban) }}</p>
                }
                @if (acc.paypalEmail) {
                  <p class="paypal-email">{{ acc.paypalEmail }}</p>
                }
              </mat-card-content>
              <mat-card-actions align="end">
                <mat-slide-toggle
                  [checked]="acc.isActive"
                  (change)="toggleActive(acc)">
                </mat-slide-toggle>
                <button mat-icon-button (click)="openForm(acc)">
                  <mat-icon>edit</mat-icon>
                </button>
                <button mat-icon-button color="warn" (click)="deleteAccount(acc)">
                  <mat-icon>delete</mat-icon>
                </button>
              </mat-card-actions>
            </mat-card>
          }
        </div>

        @if (accounts().length === 0) {
          <app-empty-state icon="account_balance" [message]="settings.labels().noAccountsEmpty" />
        }
      </app-loading-container>
    </div>
  `,
  styles: `
    .card-icon {
      font-size: 32px;
      width: 32px;
      height: 32px;
      color: var(--brand-primary-light);
    }

    .account-card {
      background: var(--clr-surface);
      border: 1px solid var(--clr-border);
      border-radius: var(--rad-lg);
      box-shadow: var(--elev-card);
      transition: box-shadow var(--transition-normal);
    }
    .account-card.has-color {
      border-left-width: 4px;
      border-left-style: solid;
    }
    .account-card:hover {
      box-shadow: var(--elev-card-hover);
    }

    .account-card.inactive {
      opacity: 0.65;
      background: var(--clr-surface-panel);
      border-style: dashed;
    }

    .iban, .paypal-email {
      font-size: var(--font-sm);
      color: var(--clr-text-muted);
      margin: var(--spc-8) 0 0;
      font-family: monospace;
      letter-spacing: 0.05em;
    }

    .currency-badge {
      display: inline-block;
      padding: var(--spc-2) var(--spc-6);
      border-radius: var(--rad-pill);
      font-size: var(--font-xs);
      font-weight: var(--fw-semibold);
      background: var(--clr-transfer-bg);
      color: var(--clr-transfer);
      margin-left: var(--spc-6);
      vertical-align: middle;
    }

    .inactive-badge {
      display: inline-block;
      padding: var(--spc-2) var(--spc-8);
      border-radius: var(--rad-lg);
      font-size: var(--font-xs);
      font-weight: var(--fw-medium);
      background: var(--clr-uncategorized-bg);
      color: var(--clr-text-disabled);
      vertical-align: middle;
      margin-left: var(--spc-6);
      text-decoration: line-through;
    }
  `,
})
export class AccountListComponent implements OnInit {
  private readonly accountService = inject(AccountService);
  private readonly refData = inject(ReferenceDataService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);

  readonly loading = signal(true);
  readonly accounts = signal<BankAccount[]>([]);

  ngOnInit(): void {
    this.loadAccounts();
  }

  loadAccounts(): void {
    this.loading.set(true);
    this.accountService.list().subscribe({
      next: (data) => {
        this.accounts.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.accounts.set([]);
        this.loading.set(false);
      },
    });
  }

  openForm(account?: BankAccount): void {
    const dialogRef = this.dialog.open(AccountFormDialogComponent, {
      width: '520px',
      maxHeight: '90vh',
      data: account ?? null,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.loadAccounts();
        this.refData.invalidate();
      }
    });
  }

  formatIbanMasked(iban: string): string {
    const clean = iban.replace(/\s/g, '');
    if (clean.length <= 8) return clean;
    const first = clean.slice(0, 4);
    const last = clean.slice(-4);
    const masked = '*'.repeat(clean.length - 8);
    const full = first + masked + last;
    return full.replace(/(.{4})/g, '$1 ').trim();
  }

  toggleActive(account: BankAccount): void {
    this.accountService.getTransactionCount(account.id).subscribe({
      next: ({ count }) => {
        const labels = this.settings.labels();
        const message = account.isActive
          ? (count > 0
              ? labels.deactivateAccount(account.accountLabel, count)
              : labels.deactivateAccountNoTx(account.accountLabel))
          : labels.activateAccount(account.accountLabel);
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
          data: {
            title: account.isActive ? labels.editAccount : labels.editAccount,
            message,
            color: account.isActive ? 'warn' : 'primary',
          } satisfies ConfirmDialogData,
        });
        dialogRef.afterClosed().subscribe((confirmed) => {
          if (!confirmed) return;
          this.accountService
            .update(account.id, { isActive: !account.isActive })
            .subscribe({
              next: () => {
                this.loadAccounts();
                this.refData.invalidate();
                const msg = account.isActive
                  ? labels.accountDeactivated(account.accountLabel)
                  : labels.accountActivated(account.accountLabel);
                this.snackBar.open(msg, labels.close, { duration: 4000 });
              },
            });
        });
      },
    });
  }

  deleteAccount(account: BankAccount): void {
    const labels = this.settings.labels();
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: labels.editAccount,
        message: labels.deleteAccountConfirm(account.accountLabel),
        color: 'warn',
      } satisfies ConfirmDialogData,
    });
    dialogRef.afterClosed().subscribe((confirmed) => {
      if (!confirmed) return;
      this.accountService.delete(account.id).subscribe({
        next: () => {
          this.loadAccounts();
          this.refData.invalidate();
        },
        error: (err) => {
          const msg = err?.error?.detail || this.settings.labels().accountDeleteError;
          this.snackBar.open(msg, this.settings.labels().close, { duration: 6000 });
        },
      });
    });
  }
}
