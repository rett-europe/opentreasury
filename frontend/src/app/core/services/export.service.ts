import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface ExportParams {
  dateFrom: string;
  dateTo: string;
  accountId?: string;
  categoryId?: string;
}

@Injectable({ providedIn: 'root' })
export class ExportService {
  private readonly api = inject(ApiService);

  /** Download transactions as Excel (.xlsx) blob */
  downloadExcel(params: ExportParams): Observable<Blob> {
    const query: Record<string, string> = {
      dateFrom: params.dateFrom,
      dateTo: params.dateTo,
    };
    if (params.accountId) query['accountId'] = params.accountId;
    if (params.categoryId) query['categoryId'] = params.categoryId;
    return this.api.downloadBlob('/export/transactions', query);
  }
}
