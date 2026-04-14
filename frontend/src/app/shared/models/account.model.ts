// Bank account — matches Cosmos DB reference_data container (type: "bank_account")
export interface BankAccount {
  id: string;
  type: string;
  bankName: string;
  bankNameShort: string;
  iban: string | null;
  paypalEmail?: string;
  accountLabel: string;
  isPaypal: boolean;
  currency: string;
  sortOrder: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string | null;
}

export interface BankAccountCreate {
  bankName: string;
  bankNameShort?: string;
  iban?: string;
  paypalEmail?: string;
  accountLabel: string;
  isPaypal: boolean;
  currency?: string;
  sortOrder?: number;
  isActive?: boolean;
}
