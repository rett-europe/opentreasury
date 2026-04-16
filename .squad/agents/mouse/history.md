# Mouse — History

## Learnings

<!-- Fresh start for opentreasury public repo. Append learnings below. -->

### 2026-04-16: Date range filter visual spec
- Wrote full visual design spec for date range filter replacing year/month dropdowns
- Key design choices: `MatButtonToggleGroup` for presets (pill-shaped, brand-primary active state), `MatDateRangeInput` in primary filter row, expandable "More filters" for secondary filters
- Filter bar reorganized from flat 2-row (12 fields always visible) to 3-zone: preset strip → primary row (4 fields) → expandable secondary (7 fields)
- Empty state: centered icon (`event_note`) + headline + subtitle, single gentle pulse animation on preset strip (respects `prefers-reduced-motion`)
- Responsive: preset buttons horizontal-scroll on mobile/tablet (never stack vertically), primary filters stack vertically on mobile
- All values reference design tokens from `_tokens.scss` — zero hardcoded values
- Spec at: `.squad/decisions/inbox/mouse-date-range-visual-spec.md`
- Active preset contrast ratio: 7.3:1 (AAA) — white on `#6d4d8c`
- Summary strip shows muted placeholder text when no range selected (prevents layout shift)
