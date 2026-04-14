import { Component, inject, OnInit, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { CurrencyPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ReportService } from '@core/services/report.service';
import {
  TransactionSummary,
  CategorySummary,
  MonthlySummary,
} from '@shared/models/report.model';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [
    MatCardModule,
    MatTabsModule,
    MatTableModule,
    MatSelectModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
    CurrencyPipe,
    FormsModule,
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h1>Informes</h1>
        <mat-form-field appearance="outline">
          <mat-label>Año</mat-label>
          <mat-select [(ngModel)]="selectedYear" (selectionChange)="loadAll()">
            @for (y of years; track y) {
              <mat-option [value]="y">{{ y }}</mat-option>
            }
          </mat-select>
        </mat-form-field>
      </div>

      <mat-tab-group>
        <!-- Summary Tab -->
        <mat-tab label="Resumen">
          @if (loadingSummary()) {
            <div class="loading-container"><mat-spinner diameter="40" /></div>
          } @else if (summary()) {
            <div class="card-grid tab-content">
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Ingresos totales</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <p class="amount income">{{ summary()!.totalIncome | currency: 'EUR' }}</p>
                </mat-card-content>
              </mat-card>
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Gastos totales</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <p class="amount expense">{{ summary()!.totalExpense | currency: 'EUR' }}</p>
                </mat-card-content>
              </mat-card>
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Saldo</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <p class="amount balance">{{ summary()!.balance | currency: 'EUR' }}</p>
                </mat-card-content>
              </mat-card>
            </div>
          }
        </mat-tab>

        <!-- By Category Tab -->
        <mat-tab label="Por categoría">
          @if (loadingCategory()) {
            <div class="loading-container"><mat-spinner diameter="40" /></div>
          } @else {
            <div class="tab-content">
              <table mat-table [dataSource]="categorySummary()" class="full-width">
                <ng-container matColumnDef="categoryName">
                  <th mat-header-cell *matHeaderCellDef>Categoría</th>
                  <td mat-cell *matCellDef="let row">{{ row.categoryName }}</td>
                </ng-container>
                <ng-container matColumnDef="totalIncome">
                  <th mat-header-cell *matHeaderCellDef>Ingresos</th>
                  <td mat-cell *matCellDef="let row" class="income-amount">
                    {{ row.totalIncome | currency: 'EUR' }}
                  </td>
                </ng-container>
                <ng-container matColumnDef="totalExpense">
                  <th mat-header-cell *matHeaderCellDef>Gastos</th>
                  <td mat-cell *matCellDef="let row" class="expense-amount">
                    {{ row.totalExpense | currency: 'EUR' }}
                  </td>
                </ng-container>
                <tr mat-header-row *matHeaderRowDef="categoryColumns"></tr>
                <tr mat-row *matRowDef="let row; columns: categoryColumns"></tr>
              </table>
            </div>
          }
        </mat-tab>

        <!-- Monthly Tab -->
        <mat-tab label="Tendencia mensual">
          @if (loadingMonthly()) {
            <div class="loading-container"><mat-spinner diameter="40" /></div>
          } @else {
            <div class="tab-content">
              <table mat-table [dataSource]="monthlySummary()" class="full-width">
                <ng-container matColumnDef="month">
                  <th mat-header-cell *matHeaderCellDef>Mes</th>
                  <td mat-cell *matCellDef="let row">{{ monthNames[row.month - 1] }} {{ row.year }}</td>
                </ng-container>
                <ng-container matColumnDef="totalIncome">
                  <th mat-header-cell *matHeaderCellDef>Ingresos</th>
                  <td mat-cell *matCellDef="let row" class="income-amount">
                    {{ row.totalIncome | currency: 'EUR' }}
                  </td>
                </ng-container>
                <ng-container matColumnDef="totalExpense">
                  <th mat-header-cell *matHeaderCellDef>Gastos</th>
                  <td mat-cell *matCellDef="let row" class="expense-amount">
                    {{ row.totalExpense | currency: 'EUR' }}
                  </td>
                </ng-container>
                <ng-container matColumnDef="balance">
                  <th mat-header-cell *matHeaderCellDef>Saldo</th>
                  <td mat-cell *matCellDef="let row" class="balance-amount">
                    {{ row.balance | currency: 'EUR' }}
                  </td>
                </ng-container>
                <tr mat-header-row *matHeaderRowDef="monthlyColumns"></tr>
                <tr mat-row *matRowDef="let row; columns: monthlyColumns"></tr>
              </table>
            </div>
          }
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: `
    .tab-content {
      padding: 24px 0;
    }

    .loading-container {
      display: flex;
      justify-content: center;
      padding: 48px;
    }

    .amount {
      font-size: 28px;
      font-weight: 500;
      margin: 16px 0 0;
    }

    .amount.income, .income-amount { color: #81c784; }
    .amount.expense, .expense-amount { color: #e57373; }
    .amount.balance, .balance-amount { color: #7986cb; }

    .income-amount, .expense-amount, .balance-amount {
      font-weight: 500;
    }
  `,
})
export class ReportsComponent implements OnInit {
  private readonly reportService = inject(ReportService);

  readonly loadingSummary = signal(true);
  readonly loadingCategory = signal(true);
  readonly loadingMonthly = signal(true);

  readonly summary = signal<TransactionSummary | null>(null);
  readonly categorySummary = signal<CategorySummary[]>([]);
  readonly monthlySummary = signal<MonthlySummary[]>([]);

  selectedYear = new Date().getFullYear();
  years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  categoryColumns = ['categoryName', 'totalIncome', 'totalExpense'];
  monthlyColumns = ['month', 'totalIncome', 'totalExpense', 'balance'];

  monthNames = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];

  ngOnInit(): void {
    this.loadAll();
  }

  loadAll(): void {
    this.loadSummary();
    this.loadByCategory();
    this.loadMonthly();
  }

  private loadSummary(): void {
    this.loadingSummary.set(true);
    this.reportService.getSummary(this.selectedYear).subscribe({
      next: (data) => {
        this.summary.set(data);
        this.loadingSummary.set(false);
      },
      error: () => this.loadingSummary.set(false),
    });
  }

  private loadByCategory(): void {
    this.loadingCategory.set(true);
    this.reportService.getByCategory(this.selectedYear).subscribe({
      next: (data) => {
        this.categorySummary.set(data);
        this.loadingCategory.set(false);
      },
      error: () => this.loadingCategory.set(false),
    });
  }

  private loadMonthly(): void {
    this.loadingMonthly.set(true);
    this.reportService.getMonthlyTrend(this.selectedYear).subscribe({
      next: (data) => {
        this.monthlySummary.set(data);
        this.loadingMonthly.set(false);
      },
      error: () => this.loadingMonthly.set(false),
    });
  }
}
