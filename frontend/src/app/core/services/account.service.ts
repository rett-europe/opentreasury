import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { BankAccount, BankAccountCreate } from '@shared/models/account.model';

@Injectable({ providedIn: 'root' })
export class AccountService {
  private readonly api = inject(ApiService);

  list(): Observable<BankAccount[]> {
    return this.api.get<BankAccount[]>('/accounts');
  }

  get(id: string): Observable<BankAccount> {
    return this.api.get<BankAccount>(`/accounts/${id}`);
  }

  create(account: BankAccountCreate): Observable<BankAccount> {
    return this.api.post<BankAccount>('/accounts', account);
  }

  update(id: string, account: Partial<BankAccountCreate>): Observable<BankAccount> {
    return this.api.put<BankAccount>(`/accounts/${id}`, account);
  }

  delete(id: string): Observable<void> {
    return this.api.delete<void>(`/accounts/${id}`);
  }

  getTransactionCount(id: string): Observable<{ count: number }> {
    return this.api.get<{ count: number }>(`/accounts/${id}/transaction-count`);
  }
}
