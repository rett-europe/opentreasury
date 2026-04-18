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
  color?: string | null;
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
  color?: string | null;
  sortOrder?: number;
  isActive?: boolean;
}

/**
 * Accessibility-safe soft color palette for bank accounts (issue #20).
 *
 * Ten soft pastel colors chosen so that dark text (#1f2937) placed on top
 * meets WCAG AA contrast (≥ 4.5:1). The list MUST stay in sync with the
 * backend palette at `api/app/constants/account_colors.py`.
 */
export const ACCOUNT_COLORS: readonly string[] = [
  '#7BB3F0', // soft blue
  '#88C9B9', // soft teal
  '#A3D977', // soft green
  '#F5D76E', // soft yellow
  '#F5B375', // soft orange
  '#F28B82', // soft red
  '#F4A6C7', // soft pink
  '#B39DDB', // soft purple
  '#B0BEC5', // soft gray
  '#A5DCE7', // soft cyan
] as const;

export const DEFAULT_ACCOUNT_COLOR = ACCOUNT_COLORS[0];

