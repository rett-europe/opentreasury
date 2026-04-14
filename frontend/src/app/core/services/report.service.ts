import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { ApiService } from './api.service';
import {
  TransactionSummary,
  CategorySummary,
  MonthlySummary,
  AccountSummary,
} from '@shared/models/report.model';

@Injectable({ providedIn: 'root' })
export class ReportService {
  private readonly api = inject(ApiService);

  getSummary(year: number, month?: number): Observable<TransactionSummary> {
    const params: Record<string, string | number | boolean | undefined> = { year };
    if (month) params['month'] = month;
    return this.api.get<{ year: number; totalIncome: number; totalExpense: number; net: number }>('/reports/summary', params).pipe(
      map(r => ({ totalIncome: r.totalIncome, totalExpenses: r.totalExpense, net: r.net }))
    );
  }

  getByCategory(year: number, month?: number): Observable<CategorySummary[]> {
    const params: Record<string, string | number | boolean | undefined> = { year };
    if (month) params['month'] = month;
    return this.api.get<{ items: CategorySummary[] }>('/reports/by-category', params).pipe(
      map(r => r.items)
    );
  }

  getMonthlyTrend(year: number): Observable<MonthlySummary[]> {
    return this.api.get<{ months: MonthlySummary[] }>('/reports/monthly-trend', { year }).pipe(
      map(r => r.months)
    );
  }

  getByAccount(year: number, month?: number): Observable<AccountSummary[]> {
    const params: Record<string, string | number | boolean | undefined> = { year };
    if (month) params['month'] = month;
    return this.api.get<{ items: AccountSummary[] }>('/reports/by-account', params).pipe(
      map(r => r.items)
    );
  }
}
