import { ChangeDetectionStrategy, Component, inject, input, output } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '@core/auth/auth.service';
import { AppSettingsService } from '@core/services/app-settings.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { TypeColorPipe } from '@shared/pipes/type-color.pipe';
import { TypeIconPipe } from '@shared/pipes/type-icon.pipe';
import { Transaction } from '@shared/models/transaction.model';

@Component({
  selector: 'app-recent-transactions-table',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatTableModule, MatIconModule, MatButtonModule,
    CurrencyPipe, DatePipe,
    TypeColorPipe, TypeIconPipe,
  ],
  template: `
    <table mat-table [dataSource]="transactions()" class="full-width">
      <ng-container matColumnDef="type">
        <th mat-header-cell *matHeaderCellDef></th>
        <td mat-cell *matCellDef="let tx">
          <mat-icon [class]="tx | typeColor">{{ tx | typeIcon }}</mat-icon>
        </td>
      </ng-container>

      <ng-container matColumnDef="date">
        <th mat-header-cell *matHeaderCellDef>{{ settings.labels().date }}</th>
        <td mat-cell *matCellDef="let tx">{{ tx.date | date: 'dd/MM/yyyy' }}</td>
      </ng-container>

      <ng-container matColumnDef="account">
        <th mat-header-cell *matHeaderCellDef>{{ settings.labels().account }}</th>
        <td mat-cell *matCellDef="let tx">{{ refData.getAccountLabel(tx.accountId) }}</td>
      </ng-container>

      <ng-container matColumnDef="description">
        <th mat-header-cell *matHeaderCellDef>{{ settings.labels().notes }}</th>
        <td mat-cell *matCellDef="let tx">{{ tx.bankDescription || tx.detail || '—' }}</td>
      </ng-container>

      <ng-container matColumnDef="category">
        <th mat-header-cell *matHeaderCellDef>{{ settings.labels().category }}</th>
        <td mat-cell *matCellDef="let tx">
          @if (tx.categoryId) {
            {{ refData.getCategoryName(tx.categoryId) }}
          } @else {
            <span class="uncategorized">{{ settings.labels().uncategorizedLabel }}</span>
          }
        </td>
      </ng-container>

      <ng-container matColumnDef="subcategory">
        <th mat-header-cell *matHeaderCellDef>{{ settings.labels().subcategory }}</th>
        <td mat-cell *matCellDef="let tx">
          @if (tx.categoryId && tx.subcategoryId) {
            {{ refData.getSubcategoryName(tx.categoryId, tx.subcategoryId) }}
          } @else {
            —
          }
        </td>
      </ng-container>

      <ng-container matColumnDef="amount">
        <th mat-header-cell *matHeaderCellDef class="text-right">{{ settings.labels().amount }}</th>
        <td mat-cell *matCellDef="let tx" class="text-right">
          <span [class.text-income]="tx.amount > 0"
                [class.text-expense]="tx.amount < 0">
            {{ tx.amount | currency: 'EUR':'symbol':'1.2-2' }}
          </span>
        </td>
      </ng-container>

      <tr mat-header-row *matHeaderRowDef="columns"></tr>
      <tr mat-row *matRowDef="let row; columns: columns"
          [class.clickable-row]="authService.isAdmin()"
          (click)="onRowClick(row)"></tr>
    </table>

    <div class="view-all-row">
      <button mat-button color="primary" (click)="viewAll.emit()">
        {{ settings.labels().transactions }} →
      </button>
    </div>
  `,
  styles: `
    .text-right {
      text-align: right;
    }
    .clickable-row {
      cursor: pointer;
    }
    .uncategorized {
      font-style: italic;
      color: var(--clr-text-muted);
    }
    .view-all-row {
      display: flex;
      justify-content: flex-end;
      padding: var(--spc-8) 0;
    }
  `,
})
export class RecentTransactionsTableComponent {
  readonly authService = inject(AuthService);
  readonly refData = inject(ReferenceDataService);
  readonly settings = inject(AppSettingsService);

  transactions = input.required<Transaction[]>();
  rowClick = output<Transaction>();
  viewAll = output<void>();

  columns = ['type', 'date', 'account', 'description', 'category', 'subcategory', 'amount'];

  onRowClick(tx: Transaction): void {
    if (this.authService.isAdmin()) {
      this.rowClick.emit(tx);
    }
  }
}
