import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  Transaction,
  TransactionCreate,
  TransactionUpdate,
  TransactionQueryParams,
  PaginatedResponse,
  ReviewStatusUpdate,
  CategorizeRequest,
  NoteCreate,
  SplitRequest,
} from '@shared/models/transaction.model';

@Injectable({ providedIn: 'root' })
export class TransactionService {
  private readonly api = inject(ApiService);

  list(params: TransactionQueryParams): Observable<PaginatedResponse<Transaction>> {
    return this.api.get<PaginatedResponse<Transaction>>('/transactions', {
      year: params.year,
      month: params.month,
      accountId: params.accountId,
      categoryId: params.categoryId,
      subcategoryId: params.subcategoryId,
      tagId: params.tagId,
      transactionType: params.transactionType,
      categorizationStatus: params.categorizationStatus,
      reviewStatus: params.reviewStatus,
      search: params.search,
      amountMin: params.amountMin,
      amountMax: params.amountMax,
      includeDeleted: params.includeDeleted,
      pageSize: params.pageSize,
      continuationToken: params.continuationToken,
    });
  }

  get(id: string, year: number, month: number): Observable<Transaction> {
    return this.api.get<Transaction>(`/transactions/${id}`, { year, month });
  }

  create(transaction: TransactionCreate): Observable<Transaction> {
    return this.api.post<Transaction>('/transactions', transaction);
  }

  update(id: string, transaction: TransactionUpdate, year: number, month: number): Observable<Transaction> {
    return this.api.put<Transaction>(`/transactions/${id}`, transaction, { year, month });
  }

  delete(id: string, year: number, month: number): Observable<void> {
    return this.api.delete<void>(`/transactions/${id}`, { year, month });
  }

  review(id: string, data: ReviewStatusUpdate, year: number, month: number): Observable<Transaction> {
    return this.api.patch<Transaction>(`/transactions/${id}/review`, data, { year, month });
  }

  categorize(id: string, data: CategorizeRequest, year: number, month: number): Observable<Transaction> {
    return this.api.patch<Transaction>(`/transactions/${id}/categorize`, data, { year, month });
  }

  addNote(id: string, data: NoteCreate, year: number, month: number): Observable<Transaction> {
    return this.api.post<Transaction>(`/transactions/${id}/notes`, data, { year, month });
  }

  split(id: string, data: SplitRequest, year: number, month: number): Observable<Transaction> {
    return this.api.post<Transaction>(`/transactions/${id}/split`, data, { year, month });
  }
}
