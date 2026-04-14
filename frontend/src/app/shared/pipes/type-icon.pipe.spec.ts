import { TypeIconPipe } from './type-icon.pipe';
import { Transaction } from '@shared/models/transaction.model';

describe('TypeIconPipe', () => {
  const pipe = new TypeIconPipe();

  function makeTx(transactionType: string): Transaction {
    return { transactionType } as Transaction;
  }

  it('should return arrow_upward for income', () => {
    expect(pipe.transform(makeTx('income'))).toBe('arrow_upward');
  });

  it('should return arrow_downward for expense', () => {
    expect(pipe.transform(makeTx('expense'))).toBe('arrow_downward');
  });

  it('should return swap_horiz for transfer', () => {
    expect(pipe.transform(makeTx('transfer'))).toBe('swap_horiz');
  });

  it('should return undo for refund', () => {
    expect(pipe.transform(makeTx('refund'))).toBe('undo');
  });

  it('should return receipt for unknown type', () => {
    expect(pipe.transform(makeTx('other'))).toBe('receipt');
  });

  it('should return receipt for undefined type', () => {
    expect(pipe.transform({} as Transaction)).toBe('receipt');
  });
});
