import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { ExcelImportSummary, ImportPreview } from '@shared/models/import.model';

@Injectable({ providedIn: 'root' })
export class ImportService {
  private readonly api = inject(ApiService);

  preview(file: File, accountId: string, sheet?: string): Observable<ImportPreview> {
    const formData = new FormData();
    formData.append('file', file);
    const params: Record<string, string | undefined> = { accountId };
    if (sheet) params['sheet'] = sheet;
    return this.api.post<ImportPreview>('/imports/preview', formData, params);
  }

  importWorkbook(
    file: File,
    accountId: string,
    categoryTypeOverrides?: Record<string, string>,
    sheet?: string,
  ): Observable<ExcelImportSummary> {
    const formData = new FormData();
    formData.append('file', file);
    if (categoryTypeOverrides && Object.keys(categoryTypeOverrides).length > 0) {
      formData.append('metadata', JSON.stringify({ categoryTypeOverrides }));
    }
    const params: Record<string, string | undefined> = { accountId };
    if (sheet) params['sheet'] = sheet;
    return this.api.post<ExcelImportSummary>('/imports/workbook', formData, params);
  }
}
