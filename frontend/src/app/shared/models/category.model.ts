// Category — matches Cosmos DB categories container
export type CategoryType = 'income' | 'expense';

export interface Category {
  id: string;
  type: string;
  name: string;
  description: string;
  sortOrder: number;
  isActive: boolean;
  categoryType: CategoryType;
  subcategories: Subcategory[];
  createdAt: string;
  updatedAt: string | null;
}

export interface Subcategory {
  id: string;
  name: string;
  isActive: boolean;
}

export interface CategoryCreate {
  name: string;
  description?: string;
  categoryType: CategoryType;
  sortOrder?: number;
  isActive?: boolean;
}

export interface SubcategoryCreate {
  id?: string | null;
  name: string;
  isActive?: boolean;
}
