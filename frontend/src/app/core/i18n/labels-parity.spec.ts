import { EN_LABELS } from './en';
import { ES_LABELS } from './es';

/**
 * Build-time i18n parity assertion required by spec
 * `docs/specs/bulk-category-update-spec.md` v1.1 §11 / NB-4.
 *
 * Both locales must expose the same set of keys — a missing translation in
 * either file should fail the frontend build. The AppLabels type already
 * enforces this at compile time, but we also assert at runtime so a drift
 * introduced via an `as AppLabels` cast or a future partial type still fails.
 */
describe('i18n label parity — EN vs ES', () => {
  const enKeys = Object.keys(EN_LABELS).sort();
  const esKeys = Object.keys(ES_LABELS).sort();

  it('exposes the same set of keys in EN and ES', () => {
    expect(esKeys).toEqual(enKeys);
  });

  it('has no ES key missing from EN', () => {
    const missing = esKeys.filter((k) => !enKeys.includes(k));
    expect(missing).toEqual([]);
  });

  it('has no EN key missing from ES', () => {
    const missing = enKeys.filter((k) => !esKeys.includes(k));
    expect(missing).toEqual([]);
  });
});
