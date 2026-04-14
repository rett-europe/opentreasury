import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatIconModule],
  template: `
    <div class="kpi-card" [class]="'kpi-' + colorClass()">
      <div class="kpi-icon-wrap">
        <mat-icon>{{ icon() }}</mat-icon>
      </div>
      <div class="kpi-content">
        <span class="kpi-label">{{ label() }}</span>
        <span class="kpi-value">{{ value() }}</span>
      </div>
    </div>
  `,
  styles: `
    .kpi-card {
      display: flex;
      align-items: center;
      gap: var(--spc-16);
      padding: var(--spc-16);
      border-radius: var(--rad-lg);
      background: var(--clr-surface-panel);
      cursor: default;
      transition: box-shadow var(--transition-normal);
    }
    .kpi-card:hover {
      box-shadow: var(--elev-card-hover);
    }
    .kpi-icon-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
      width: var(--spc-48);
      height: var(--spc-48);
      border-radius: var(--rad-lg);
    }
    .kpi-icon-wrap mat-icon {
      font-size: var(--font-xl);
      width: var(--font-xl);
      height: var(--font-xl);
    }
    .kpi-income .kpi-icon-wrap {
      background: var(--clr-income-bg);
      color: var(--clr-income);
    }
    .kpi-expense .kpi-icon-wrap {
      background: var(--clr-expense-bg);
      color: var(--clr-expense);
    }
    .kpi-net .kpi-icon-wrap {
      background: var(--brand-surface);
      color: var(--brand-primary-light);
    }
    .kpi-content {
      display: flex;
      flex-direction: column;
    }
    .kpi-label {
      font-size: var(--font-xs);
      font-weight: var(--fw-bold);
      text-transform: uppercase;
      letter-spacing: var(--ls-section);
      color: var(--clr-text-muted);
    }
    .kpi-value {
      font-size: var(--font-xl);
      font-weight: var(--fw-semibold);
      line-height: var(--lh-tight);
    }
  `,
})
export class KpiCardComponent {
  label = input.required<string>();
  value = input.required<string>();
  icon = input.required<string>();
  colorClass = input.required<string>();
}
