import { Pipe, PipeTransform } from '@angular/core';
import { Transaction } from '@shared/models/transaction.model';

@Pipe({ name: 'typeIcon', standalone: true, pure: true })
export class TypeIconPipe implements PipeTransform {
  transform(tx: Transaction): string {
    switch (tx.transactionType) {
      case 'income':   return 'arrow_upward';
      case 'expense':  return 'arrow_downward';
      case 'transfer': return 'swap_horiz';
      case 'refund':   return 'undo';
      default:         return 'receipt';
    }
  }
}
