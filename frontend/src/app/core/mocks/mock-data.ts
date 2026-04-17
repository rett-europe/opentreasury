/**
 * Mock data for offline development.
 * Realistic Spanish NGO (Rett syndrome association) treasury data.
 */
import { BankAccount } from '@shared/models/account.model';
import { Category } from '@shared/models/category.model';
import { Tag } from '@shared/models/tag.model';
import { Transaction, TransactionType } from '@shared/models/transaction.model';
import { UserProfile } from '@shared/models/user.model';
import { ReferenceData } from '@shared/models/reference-data.model';
import {
  TransactionSummary,
  CategorySummary,
  BalanceItem,
  MonthlySummary,
  AccountSummary,
} from '@shared/models/report.model';

// ---------------------------------------------------------------------------
// IDs
// ---------------------------------------------------------------------------
const ACC_UNICAJA = 'acc-unicaja-principal';
const ACC_CAIXA_OPS = 'acc-caixa-operaciones';
const ACC_CAIXA_AHORRO = 'acc-caixa-ahorro';
const ACC_CAIXA_EVENTOS = 'acc-caixa-eventos';
const ACC_PAYPAL = 'acc-paypal-donaciones';

const CAT_ACTIVIDADES = 'cat-actividades';
const CAT_ADMIN = 'cat-administrativo';
const CAT_CUOTAS = 'cat-cuotas';
const CAT_DONACIONES = 'cat-donaciones';
const CAT_EVENTOS = 'cat-eventos';
const CAT_GASTOS = 'cat-gastos';
const CAT_SUBVENCIONES = 'cat-subvenciones';

// ---------------------------------------------------------------------------
// Bank Accounts
// ---------------------------------------------------------------------------
export const MOCK_ACCOUNTS: BankAccount[] = [
  {
    id: ACC_UNICAJA,
    type: 'bank_account',
    bankName: 'Unicaja Banco',
    bankNameShort: 'Unicaja',
    iban: 'ES91 2103 0001 00 0123456789',
    accountLabel: 'Principal',
    isPaypal: false,
    currency: 'EUR',
    sortOrder: 1,
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: ACC_CAIXA_OPS,
    type: 'bank_account',
    bankName: 'CaixaBank',
    bankNameShort: 'CaixaBank',
    iban: 'ES12 2100 0418 45 0200051332',
    accountLabel: 'Operaciones',
    isPaypal: false,
    currency: 'EUR',
    sortOrder: 2,
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: ACC_CAIXA_AHORRO,
    type: 'bank_account',
    bankName: 'CaixaBank',
    bankNameShort: 'CaixaBank',
    iban: 'ES34 2100 0418 45 0200062845',
    accountLabel: 'Ahorro',
    isPaypal: false,
    currency: 'EUR',
    sortOrder: 3,
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: ACC_CAIXA_EVENTOS,
    type: 'bank_account',
    bankName: 'CaixaBank',
    bankNameShort: 'CaixaBank',
    iban: 'ES56 2100 0418 45 0200073591',
    accountLabel: 'Eventos',
    isPaypal: false,
    currency: 'EUR',
    sortOrder: 4,
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: ACC_PAYPAL,
    type: 'bank_account',
    bankName: 'PayPal',
    bankNameShort: 'PayPal',
    iban: null,
    paypalEmail: 'donations@example.org',
    accountLabel: 'Donaciones',
    isPaypal: true,
    currency: 'EUR',
    sortOrder: 5,
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
];

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------
export const MOCK_CATEGORIES: Category[] = [
  {
    id: CAT_ACTIVIDADES,
    type: 'category',
    name: 'Actividades',
    description: 'Actividades de la asociación',
    sortOrder: 1,
    isActive: true,
    categoryType: 'expense',
    subcategories: [
      { id: 'sub-talleres', name: 'Talleres', isActive: true },
      { id: 'sub-terapias', name: 'Terapias', isActive: true },
      { id: 'sub-formacion', name: 'Formación', isActive: true },
    ],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: CAT_ADMIN,
    type: 'category',
    name: 'Administrativo',
    description: 'Gastos administrativos',
    sortOrder: 2,
    isActive: true,
    categoryType: 'expense',
    subcategories: [
      { id: 'sub-material', name: 'Material oficina', isActive: true },
      { id: 'sub-profesionales', name: 'Servicios profesionales', isActive: true },
      { id: 'sub-seguros', name: 'Seguros', isActive: true },
    ],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: CAT_CUOTAS,
    type: 'category',
    name: 'Cuotas',
    description: 'Cuotas de socios y familias',
    sortOrder: 3,
    isActive: true,
    categoryType: 'income',
    subcategories: [
      { id: 'sub-cuota-socios', name: 'Cuota socios', isActive: true },
      { id: 'sub-cuota-familias', name: 'Cuota familias', isActive: true },
    ],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: CAT_DONACIONES,
    type: 'category',
    name: 'Donaciones',
    description: 'Donaciones recibidas',
    sortOrder: 4,
    isActive: true,
    categoryType: 'income',
    subcategories: [
      { id: 'sub-don-individual', name: 'Donaciones individuales', isActive: true },
      { id: 'sub-don-empresa', name: 'Donaciones empresas', isActive: true },
      { id: 'sub-don-anonima', name: 'Donaciones anónimas', isActive: true },
    ],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: CAT_EVENTOS,
    type: 'category',
    name: 'Eventos',
    description: 'Eventos organizados',
    sortOrder: 5,
    isActive: true,
    categoryType: 'expense',
    subcategories: [
      { id: 'sub-charlas', name: 'Charlas', isActive: true },
      { id: 'sub-galas', name: 'Galas benéficas', isActive: true },
      { id: 'sub-carreras', name: 'Carreras solidarias', isActive: true },
    ],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: CAT_GASTOS,
    type: 'category',
    name: 'Gastos',
    description: 'Gastos generales',
    sortOrder: 6,
    isActive: true,
    categoryType: 'expense',
    subcategories: [
      { id: 'sub-alquiler', name: 'Alquiler', isActive: true },
      { id: 'sub-suministros', name: 'Suministros', isActive: true },
      { id: 'sub-transporte', name: 'Transporte', isActive: true },
      { id: 'sub-comunicacion', name: 'Comunicación', isActive: true },
    ],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
  {
    id: CAT_SUBVENCIONES,
    type: 'category',
    name: 'Subvenciones',
    description: 'Subvenciones recibidas',
    sortOrder: 7,
    isActive: true,
    categoryType: 'income',
    subcategories: [
      { id: 'sub-subv-publica', name: 'Subvenciones públicas', isActive: true },
      { id: 'sub-subv-privada', name: 'Subvenciones privadas', isActive: true },
    ],
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: null,
  },
];

// ---------------------------------------------------------------------------
// Tags
// ---------------------------------------------------------------------------
export const MOCK_TAGS: Tag[] = [
  { id: 'tag-cal2025', type: 'tag', name: 'Calendarios 2025', color: '#b39ddb', sortOrder: 1, isActive: true, createdAt: '2024-11-01T10:00:00Z', updatedAt: null },
  { id: 'tag-raras2025', type: 'tag', name: 'Día Enfermedades Raras 2025', color: '#ce93d8', sortOrder: 2, isActive: true, createdAt: '2024-11-01T10:00:00Z', updatedAt: null },
  { id: 'tag-camisetas', type: 'tag', name: 'Camisetas Padre', color: '#81c784', sortOrder: 3, isActive: true, createdAt: '2024-11-01T10:00:00Z', updatedAt: null },
  { id: 'tag-gala2025', type: 'tag', name: 'Gala Benéfica 2025', color: '#ffb74d', sortOrder: 4, isActive: true, createdAt: '2024-11-01T10:00:00Z', updatedAt: null },
  { id: 'tag-navidad2025', type: 'tag', name: 'Campaña Navidad 2025', color: '#ef9a9a', sortOrder: 5, isActive: true, createdAt: '2024-11-01T10:00:00Z', updatedAt: null },
  { id: 'tag-semanarett', type: 'tag', name: 'Semana Rett', color: '#80cbc4', sortOrder: 6, isActive: true, createdAt: '2024-11-01T10:00:00Z', updatedAt: null },
  { id: 'tag-mercadillo', type: 'tag', name: 'Mercadillo Solidario', color: '#a1887f', sortOrder: 7, isActive: true, createdAt: '2024-11-01T10:00:00Z', updatedAt: null },
  { id: 'tag-retodeportivo', type: 'tag', name: 'Reto Deportivo', color: '#90caf9', sortOrder: 8, isActive: true, createdAt: '2024-11-01T10:00:00Z', updatedAt: null },
];

// ---------------------------------------------------------------------------
// User
// ---------------------------------------------------------------------------
export const MOCK_USERS: UserProfile[] = [
  {
    id: 'mock-oid-pedro',
    displayName: 'Pedro',
    email: 'pedro@example.org',
    role: 'Admin',
  },
  {
    id: 'mock-oid-srivas',
    displayName: 'Sergio Rivas',
    email: 'srivas@example.org',
    role: 'Admin',
  },
];

export const MOCK_USER: UserProfile = MOCK_USERS[1];

// ---------------------------------------------------------------------------
// Reference Data (combined)
// ---------------------------------------------------------------------------
export const MOCK_REFERENCE_DATA: ReferenceData = {
  accounts: MOCK_ACCOUNTS,
  categories: MOCK_CATEGORIES,
  tags: MOCK_TAGS,
};

// ---------------------------------------------------------------------------
// Transactions
// ---------------------------------------------------------------------------
function tx(
  id: string,
  date: string,
  amount: number,
  bankDesc: string,
  accountId: string,
  categoryId: string,
  subcategoryId: string | null,
  tagIds: string[],
  opts?: Partial<Transaction>,
): Transaction {
  const d = new Date(date);
  const transactionType: TransactionType = amount >= 0 ? 'income' : 'expense';
  return {
    id,
    type: 'transaction',
    partitionKey: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
    transactionType: opts?.transactionType ?? transactionType,
    date,
    valueDate: opts?.valueDate ?? date,
    amount,
    currency: 'EUR',
    balance: opts?.balance ?? null,
    movementNumber: opts?.movementNumber ?? null,
    branchNumber: null,
    bankDescription: bankDesc,
    accountId,
    categoryId,
    subcategoryId,
    categorizationStatus: opts?.categorizationStatus ?? 'manually_categorized',
    reviewStatus: opts?.reviewStatus ?? 'approved',
    sourceReference: opts?.sourceReference ?? null,
    counterpartyName: opts?.counterpartyName ?? null,
    counterpartyReference: opts?.counterpartyReference ?? null,
    tagIds,
    detail: opts?.detail ?? null,
    originalAmount: opts?.originalAmount ?? null,
    originalDate: opts?.originalDate ?? null,
    notes: opts?.notes ?? [],
    isSplit: false,
    splitCount: 0,
    splitLines: [],
    splitCategoryIds: [],
    year: d.getFullYear(),
    month: d.getMonth() + 1,
    createdBy: 'mock-oid-pedro',
    createdByName: 'Demo Admin',
    createdAt: '2026-03-01T09:00:00Z',
    updatedBy: null,
    updatedByName: null,
    updatedAt: null,
    reviewedBy: opts?.reviewedBy ?? 'mock-oid-pedro',
    reviewedByName: opts?.reviewedByName ?? 'Demo Admin',
    reviewedAt: opts?.reviewedAt ?? '2026-03-01T09:00:00Z',
    isDeleted: false,
  };
}

export const MOCK_TRANSACTIONS: Transaction[] = [
  // ---- March 2026 ----
  tx('tx-001', '2026-03-01', -850.00, 'RECIBO DOMICILIADO: ALQUILER LOCAL ASOC. RETT MARZO 2026', ACC_CAIXA_OPS, CAT_GASTOS, 'sub-alquiler', [], { balance: 12450.30, movementNumber: 'M20260301001' }),
  tx('tx-002', '2026-03-02', 50.00, 'TRANSFERENCIA A FAVOR DE ASOC. RETT - CUOTA SOCIO DEMO PERSONA', ACC_UNICAJA, CAT_CUOTAS, 'sub-cuota-socios', [], { balance: 8320.50 }),
  tx('tx-003', '2026-03-03', 150.00, 'TRANSFERENCIA A FAVOR - DONACION ANONIMA', ACC_PAYPAL, CAT_DONACIONES, 'sub-don-anonima', ['tag-raras2025'], { detail: 'Donación con motivo Día Enfermedades Raras' }),
  tx('tx-004', '2026-03-05', -125.50, 'PAGO TPV: AMAZON BUSINESS EU - MATERIAL OFICINA', ACC_CAIXA_OPS, CAT_ADMIN, 'sub-material', []),
  tx('tx-005', '2026-03-06', 2500.00, 'TRANSFERENCIA A FAVOR: DONACION EMPRESA TECH SOLUTIONS SL', ACC_UNICAJA, CAT_DONACIONES, 'sub-don-empresa', ['tag-raras2025'], { balance: 10820.50, detail: 'Donación corporativa - campaña Día Enfermedades Raras' }),
  tx('tx-006', '2026-03-08', -320.00, 'TRANSFERENCIA EMITIDA: TERAPEUTA MARIA GONZALEZ - SESIONES MARZO', ACC_CAIXA_OPS, CAT_ACTIVIDADES, 'sub-terapias', [], { balance: 11704.80 }),
  tx('tx-007', '2026-03-10', -89.90, 'RECIBO DOMICILIADO: VODAFONE ESPAÑA - LINEA OFICINA', ACC_CAIXA_OPS, CAT_GASTOS, 'sub-comunicacion', [], { balance: 11614.90 }),
  tx('tx-008', '2026-03-11', 75.00, 'TRANSFERENCIA A FAVOR: CUOTA FAMILIA DEMO FAMILIA', ACC_UNICAJA, CAT_CUOTAS, 'sub-cuota-familias', []),
  tx('tx-009', '2026-03-12', 1200.00, 'INGRESO EFECTIVO: VENTA CALENDARIOS SOLIDARIOS', ACC_CAIXA_EVENTOS, CAT_EVENTOS, 'sub-charlas', ['tag-cal2025'], { detail: 'Recaudación venta calendarios - lote 3' }),
  tx('tx-010', '2026-03-14', -450.00, 'TRANSFERENCIA EMITIDA: IMPRENTA GARCIA - CALENDARIOS 2025', ACC_CAIXA_OPS, CAT_ADMIN, 'sub-profesionales', ['tag-cal2025']),
  tx('tx-011', '2026-03-15', -178.30, 'RECIBO DOMICILIADO: IBERDROLA - SUMINISTRO ELECTRICO OFICINA', ACC_CAIXA_OPS, CAT_GASTOS, 'sub-suministros', [], { balance: 10986.50 }),
  tx('tx-012', '2026-03-17', 500.00, 'TRANSFERENCIA A FAVOR: SUBVENCION AYTO. VALENCIA - ACTIVIDADES 2026', ACC_UNICAJA, CAT_SUBVENCIONES, 'sub-subv-publica', [], { detail: 'Primera cuota subvención municipal actividades' }),
  tx('tx-013', '2026-03-19', 85.00, 'PAYPAL: DONACION WEB - JUAN PEREZ', ACC_PAYPAL, CAT_DONACIONES, 'sub-don-individual', []),
  tx('tx-014', '2026-03-20', -65.00, 'PAGO TPV: CERCANIAS RENFE - DESPLAZAMIENTO CONGRESO', ACC_CAIXA_OPS, CAT_GASTOS, 'sub-transporte', ['tag-semanarett']),
  tx('tx-015', '2026-03-22', -1500.00, 'TRANSFERENCIA EMITIDA: SEGURO RC ASOCIACION 2026', ACC_CAIXA_AHORRO, CAT_ADMIN, 'sub-seguros', [], { balance: 5230.00 }),
  tx('tx-016', '2026-03-25', 3200.00, 'TRANSFERENCIA A FAVOR: RECAUDACION GALA BENEFICA 2025 (PENDIENTE)', ACC_CAIXA_EVENTOS, CAT_EVENTOS, 'sub-galas', ['tag-gala2025'], { detail: 'Ingreso pendiente de la gala celebrada en diciembre 2025' }),
  tx('tx-017', '2026-03-27', 50.00, 'TRANSFERENCIA A FAVOR: CUOTA SOCIO FERNANDEZ', ACC_UNICAJA, CAT_CUOTAS, 'sub-cuota-socios', []),
  tx('tx-018', '2026-03-28', -220.00, 'TRANSFERENCIA EMITIDA: TALLER MUSICOTERAPIA - INSTRUCTOR', ACC_CAIXA_OPS, CAT_ACTIVIDADES, 'sub-talleres', []),
  // ---- April 2026 ----
  tx('tx-019', '2026-04-01', -850.00, 'RECIBO DOMICILIADO: ALQUILER LOCAL ASOC. RETT ABRIL 2026', ACC_CAIXA_OPS, CAT_GASTOS, 'sub-alquiler', [], { balance: 9766.50, movementNumber: 'M20260401001' }),
  tx('tx-020', '2026-04-02', 200.00, 'PAYPAL: DONACION WEB - CAMPAÑA RETO DEPORTIVO', ACC_PAYPAL, CAT_DONACIONES, 'sub-don-individual', ['tag-retodeportivo']),
  tx('tx-021', '2026-04-03', -340.00, 'TRANSFERENCIA EMITIDA: TERAPEUTA MARIA GONZALEZ - SESIONES ABRIL', ACC_CAIXA_OPS, CAT_ACTIVIDADES, 'sub-terapias', [], { balance: 9426.50 }),
  tx('tx-022', '2026-04-05', 5000.00, 'TRANSFERENCIA A FAVOR: SUBVENCION COMUNITAT VALENCIANA ENFERMEDADES RARAS', ACC_UNICAJA, CAT_SUBVENCIONES, 'sub-subv-publica', ['tag-raras2025'], { balance: 16320.50, detail: 'Subvención autonómica programa enfermedades raras 2026' }),
  tx('tx-023', '2026-04-07', -45.00, 'PAGO TPV: CORREOS - ENVIO CAMISETAS SOLIDARIAS', ACC_CAIXA_OPS, CAT_GASTOS, 'sub-transporte', ['tag-camisetas']),
  tx('tx-024', '2026-04-08', 750.00, 'INGRESO EFECTIVO: MERCADILLO SOLIDARIO ABRIL', ACC_CAIXA_EVENTOS, CAT_EVENTOS, 'sub-charlas', ['tag-mercadillo'], { detail: 'Recaudación mercadillo solidario - Plaza Mayor' }),
  tx('tx-025', '2026-04-09', -92.40, 'RECIBO DOMICILIADO: VODAFONE ESPAÑA - LINEA OFICINA', ACC_CAIXA_OPS, CAT_GASTOS, 'sub-comunicacion', [], { balance: 9289.10 }),
];

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------
export const MOCK_REPORT_SUMMARY: TransactionSummary = {
  totalIncome: 18760.00,
  totalExpenses: 5126.10,
  net: 13633.90,
};

export const MOCK_REPORT_BY_CATEGORY: CategorySummary[] = [
  { categoryId: CAT_ACTIVIDADES, categoryName: 'Actividades', totalIncome: 0, totalExpenses: 880.00 },
  { categoryId: CAT_ADMIN, categoryName: 'Administrativo', totalIncome: 0, totalExpenses: 2075.50 },
  { categoryId: CAT_CUOTAS, categoryName: 'Cuotas', totalIncome: 175.00, totalExpenses: 0 },
  { categoryId: CAT_DONACIONES, categoryName: 'Donaciones', totalIncome: 2935.00, totalExpenses: 0 },
  { categoryId: CAT_EVENTOS, categoryName: 'Eventos', totalIncome: 5150.00, totalExpenses: 0 },
  { categoryId: CAT_GASTOS, categoryName: 'Gastos', totalIncome: 0, totalExpenses: 2170.60 },
  { categoryId: CAT_SUBVENCIONES, categoryName: 'Subvenciones', totalIncome: 5500.00, totalExpenses: 0 },
];

export const MOCK_REPORT_BALANCE: BalanceItem[] = [
  { categoryId: 'uncategorized', categoryName: 'Uncategorized', income: 120.00, expense: 45.00, net: 75.00 },
  { categoryId: CAT_ACTIVIDADES, categoryName: 'Actividades', subcategoryId: 'sub-talleres', subcategoryName: 'Talleres', income: 0, expense: 220.00, net: -220.00 },
  { categoryId: CAT_ACTIVIDADES, categoryName: 'Actividades', subcategoryId: 'sub-terapias', subcategoryName: 'Terapias', income: 0, expense: 660.00, net: -660.00 },
  { categoryId: CAT_ADMIN, categoryName: 'Administrativo', subcategoryId: 'sub-material', subcategoryName: 'Material oficina', income: 0, expense: 125.50, net: -125.50 },
  { categoryId: CAT_ADMIN, categoryName: 'Administrativo', subcategoryId: 'sub-profesionales', subcategoryName: 'Servicios profesionales', income: 0, expense: 450.00, net: -450.00 },
  { categoryId: CAT_ADMIN, categoryName: 'Administrativo', subcategoryId: 'sub-seguros', subcategoryName: 'Seguros', income: 0, expense: 1500.00, net: -1500.00 },
  { categoryId: CAT_CUOTAS, categoryName: 'Cuotas', subcategoryId: 'sub-cuota-familias', subcategoryName: 'Cuota familias', income: 75.00, expense: 0, net: 75.00 },
  { categoryId: CAT_CUOTAS, categoryName: 'Cuotas', subcategoryId: 'sub-cuota-socios', subcategoryName: 'Cuota socios', income: 100.00, expense: 0, net: 100.00 },
  { categoryId: CAT_DONACIONES, categoryName: 'Donaciones', subcategoryId: 'sub-don-anonima', subcategoryName: 'Donaciones anónimas', income: 150.00, expense: 0, net: 150.00 },
  { categoryId: CAT_DONACIONES, categoryName: 'Donaciones', subcategoryId: 'sub-don-empresa', subcategoryName: 'Donaciones empresas', income: 2500.00, expense: 0, net: 2500.00 },
  { categoryId: CAT_DONACIONES, categoryName: 'Donaciones', subcategoryId: 'sub-don-individual', subcategoryName: 'Donaciones individuales', income: 285.00, expense: 0, net: 285.00 },
  { categoryId: CAT_EVENTOS, categoryName: 'Eventos', subcategoryId: 'sub-charlas', subcategoryName: 'Charlas', income: 1950.00, expense: 0, net: 1950.00 },
  { categoryId: CAT_EVENTOS, categoryName: 'Eventos', subcategoryId: 'sub-galas', subcategoryName: 'Galas benéficas', income: 3200.00, expense: 0, net: 3200.00 },
  { categoryId: CAT_GASTOS, categoryName: 'Gastos', subcategoryId: 'sub-alquiler', subcategoryName: 'Alquiler', income: 0, expense: 1700.00, net: -1700.00 },
  { categoryId: CAT_GASTOS, categoryName: 'Gastos', subcategoryId: 'sub-comunicacion', subcategoryName: 'Comunicación', income: 0, expense: 182.30, net: -182.30 },
  { categoryId: CAT_GASTOS, categoryName: 'Gastos', subcategoryId: 'sub-suministros', subcategoryName: 'Suministros', income: 0, expense: 178.30, net: -178.30 },
  { categoryId: CAT_GASTOS, categoryName: 'Gastos', subcategoryId: 'sub-transporte', subcategoryName: 'Transporte', income: 0, expense: 110.00, net: -110.00 },
  { categoryId: CAT_SUBVENCIONES, categoryName: 'Subvenciones', subcategoryId: 'sub-subv-publica', subcategoryName: 'Subvenciones públicas', income: 5500.00, expense: 0, net: 5500.00 },
];

export const MOCK_REPORT_MONTHLY: MonthlySummary[] = [
  { year: 2026, month: 1, totalIncome: 3200.00, totalExpenses: 1850.00, net: 1350.00 },
  { year: 2026, month: 2, totalIncome: 4100.00, totalExpenses: 2100.00, net: 2000.00 },
  { year: 2026, month: 3, totalIncome: 7810.00, totalExpenses: 3798.70, net: 4011.30 },
  { year: 2026, month: 4, totalIncome: 5950.00, totalExpenses: 1327.40, net: 4622.60 },
];

export const MOCK_REPORT_BY_ACCOUNT: AccountSummary[] = [
  { accountId: ACC_UNICAJA, totalIncome: 8250.00, totalExpense: 0, net: 8250.00, transactionCount: 5 },
  { accountId: ACC_CAIXA_OPS, totalIncome: 0, totalExpense: 3270.10, net: -3270.10, transactionCount: 10 },
  { accountId: ACC_CAIXA_AHORRO, totalIncome: 0, totalExpense: 1500.00, net: -1500.00, transactionCount: 1 },
  { accountId: ACC_CAIXA_EVENTOS, totalIncome: 4950.00, totalExpense: 0, net: 4950.00, transactionCount: 3 },
  { accountId: ACC_PAYPAL, totalIncome: 435.00, totalExpense: 0, net: 435.00, transactionCount: 3 },
];

// ---------------------------------------------------------------------------
// Audit trail
// ---------------------------------------------------------------------------
export interface MockAuditEntry {
  id: string;
  entityType: string;
  entityId: string;
  action: string;
  changedBy: string;
  changedByName: string;
  changedAt: string;
  oldValues: Record<string, unknown> | null;
  newValues: Record<string, unknown> | null;
}

export const MOCK_AUDIT: MockAuditEntry[] = [
  { id: 'aud-001', entityType: 'transaction', entityId: 'tx-001', action: 'create', changedBy: 'mock-oid-pedro', changedByName: 'Demo Admin', changedAt: '2026-03-01T09:15:00Z', oldValues: null, newValues: { amount: -850 } },
  { id: 'aud-002', entityType: 'category', entityId: CAT_EVENTOS, action: 'update', changedBy: 'mock-oid-pedro', changedByName: 'Demo Admin', changedAt: '2026-03-02T11:00:00Z', oldValues: { sortOrder: 6 }, newValues: { sortOrder: 5 } },
  { id: 'aud-003', entityType: 'transaction', entityId: 'tx-005', action: 'create', changedBy: 'mock-oid-pedro', changedByName: 'Demo Admin', changedAt: '2026-03-06T14:30:00Z', oldValues: null, newValues: { amount: 2500 } },
  { id: 'aud-004', entityType: 'tag', entityId: 'tag-retodeportivo', action: 'create', changedBy: 'mock-oid-pedro', changedByName: 'Demo Admin', changedAt: '2026-03-10T08:00:00Z', oldValues: null, newValues: { name: 'Reto Deportivo' } },
  { id: 'aud-005', entityType: 'transaction', entityId: 'tx-016', action: 'create', changedBy: 'mock-oid-pedro', changedByName: 'Demo Admin', changedAt: '2026-03-25T16:45:00Z', oldValues: null, newValues: { amount: 3200 } },
];
