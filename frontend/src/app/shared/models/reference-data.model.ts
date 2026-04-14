import { BankAccount } from './account.model';
import { Category } from './category.model';
import { Tag } from './tag.model';

// Combined reference data response from GET /api/reference-data
export interface ReferenceData {
  accounts: BankAccount[];
  categories: Category[];
  tags: Tag[];
}
