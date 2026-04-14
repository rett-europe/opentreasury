import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api.service';
import { ReferenceData } from '@shared/models/reference-data.model';
import { BankAccount } from '@shared/models/account.model';
import { Category } from '@shared/models/category.model';
import { Tag } from '@shared/models/tag.model';

/**
 * Loads all dropdown reference data (accounts, categories, tags) in one call.
 * Caches in memory. Call invalidate() after any mutation to refresh.
 */
@Injectable({ providedIn: 'root' })
export class ReferenceDataService {
  private readonly api = inject(ApiService);

  private readonly _accounts = signal<BankAccount[]>([]);
  private readonly _categories = signal<Category[]>([]);
  private readonly _tags = signal<Tag[]>([]);
  private readonly _loaded = signal(false);

  readonly accounts = this._accounts.asReadonly();
  readonly categories = this._categories.asReadonly();
  readonly tags = this._tags.asReadonly();
  readonly loaded = this._loaded.asReadonly();

  /** Load all reference data from GET /api/reference-data. No-op if already loaded. */
  load(): void {
    if (this._loaded()) return;
    this.api.get<ReferenceData>('/reference-data').subscribe({
      next: (data) => {
        this._accounts.set(data.accounts);
        this._categories.set(data.categories);
        this._tags.set(data.tags);
        this._loaded.set(true);
      },
    });
  }

  /** Clear cache and re-fetch. Call after creating/updating/deleting reference entities. */
  invalidate(): void {
    this._loaded.set(false);
    this.load();
  }

  // --- Lookup helpers ---

  getAccountLabel(id: string): string {
    return this._accounts().find((a) => a.id === id)?.accountLabel ?? '';
  }

  getCategoryName(id: string): string {
    return this._categories().find((c) => c.id === id)?.name ?? '';
  }

  getSubcategoryName(categoryId: string, subcategoryId: string | null): string {
    if (!subcategoryId) return '';
    const cat = this._categories().find((c) => c.id === categoryId);
    return cat?.subcategories.find((s) => s.id === subcategoryId)?.name ?? '—';
  }

  getTagName(id: string): string {
    return this._tags().find((t) => t.id === id)?.name ?? '';
  }

  getTagColor(id: string): string {
    return this._tags().find((t) => t.id === id)?.color ?? '#9e9e9e';
  }

  getTagTextColor(id: string): string {
    const hex = this.getTagColor(id);
    return this.contrastColor(hex);
  }

  contrastColor(hex: string): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5 ? '#000000' : '#ffffff';
  }
}
