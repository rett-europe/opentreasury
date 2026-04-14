# Security Audits & Compliance

Security scan reports and remediation tracking for NGO Treasury.

## Scan History

| Date | Scanners | Reviewer | CRITICAL | HIGH | MEDIUM | LOW | Total | Status |
|------|----------|----------|----------|------|--------|-----|-------|--------|
| [2026-04-12](scan-2026-04-12.md) | Neo, Morpheus, Trinity, Tank | Switch | 5 | 11 | 10 | 7 | 33 | Open |

## Reviews

| Date | Reviewer | Scope | Report |
|------|----------|-------|--------|
| 2026-04-12 | Switch | Expert review of generalist scan | [review-switch-2026-04-12.md](review-switch-2026-04-12.md) |

## Naming Convention

- Security scan reports: `scan-YYYY-MM-DD.md`
- Ad-hoc reviews: `review-{topic}-YYYY-MM-DD.md`

## Process

1. Scans are performed periodically or before major releases
2. **Switch (Security Engineer) must review** all scan findings — generalist scans require expert validation
3. Findings are tracked here; remediation links to PRs/issues
4. Resolved findings are verified in the next scan
