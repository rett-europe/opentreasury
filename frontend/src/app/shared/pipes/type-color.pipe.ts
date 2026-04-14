import { Pipe, PipeTransform } from '@angular/core';
import { Transaction } from '@shared/models/transaction.model';

@Pipe({ name: 'typeColor', standalone: true, pure: true })
export class TypeColorPipe implements PipeTransform {
  transform(tx: Transaction): string {
    switch (tx.transactionType) {
      case 'income':   return 'type-income';
      case 'expense':  return 'type-expense';
      case 'transfer': return 'type-transfer';
      case 'refund':   return 'type-refund';
      default:         return '';
    }
  }
}
