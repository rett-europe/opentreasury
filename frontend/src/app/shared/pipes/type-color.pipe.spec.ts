import { TypeColorPipe } from './type-color.pipe';
import { Transaction } from '@shared/models/transaction.model';

describe('TypeColorPipe', () => {
  const pipe = new TypeColorPipe();

  function makeTx(transactionType: string): Transaction {
    return { transactionType } as Transaction;
  }

  it('should return type-income for income', () => {
    expect(pipe.transform(makeTx('income'))).toBe('type-income');
  });

  it('should return type-expense for expense', () => {
    expect(pipe.transform(makeTx('expense'))).toBe('type-expense');
  });

  it('should return type-transfer for transfer', () => {
    expect(pipe.transform(makeTx('transfer'))).toBe('type-transfer');
  });

  it('should return type-refund for refund', () => {
    expect(pipe.transform(makeTx('refund'))).toBe('type-refund');
  });

  it('should return empty string for unknown type', () => {
    expect(pipe.transform(makeTx('other'))).toBe('');
  });

  it('should return empty string for undefined type', () => {
    expect(pipe.transform({} as Transaction)).toBe('');
  });
});
