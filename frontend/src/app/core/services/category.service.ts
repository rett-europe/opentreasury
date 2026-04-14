import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { Category, CategoryCreate, SubcategoryCreate } from '@shared/models/category.model';

@Injectable({ providedIn: 'root' })
export class CategoryService {
  private readonly api = inject(ApiService);

  list(): Observable<Category[]> {
    return this.api.get<Category[]>('/categories');
  }

  get(id: string): Observable<Category> {
    return this.api.get<Category>(`/categories/${id}`);
  }

  create(category: CategoryCreate): Observable<Category> {
    return this.api.post<Category>('/categories', category);
  }

  update(id: string, category: Partial<CategoryCreate>): Observable<Category> {
    return this.api.put<Category>(`/categories/${id}`, category);
  }

  delete(id: string): Observable<void> {
    return this.api.delete<void>(`/categories/${id}`);
  }

  addSubcategory(categoryId: string, subcategory: SubcategoryCreate): Observable<Category> {
    return this.api.post<Category>(`/categories/${categoryId}/subcategories`, subcategory);
  }

  updateSubcategory(
    categoryId: string,
    subId: string,
    subcategory: Partial<SubcategoryCreate>,
  ): Observable<Category> {
    return this.api.put<Category>(
      `/categories/${categoryId}/subcategories/${subId}`,
      subcategory,
    );
  }

  deleteSubcategory(categoryId: string, subId: string): Observable<void> {
    return this.api.delete<void>(`/categories/${categoryId}/subcategories/${subId}`);
  }
}
