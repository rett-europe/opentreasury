import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatIconModule],
  template: `
    <span class="status-badge" [class]="'status-' + status()">
      <mat-icon>{{ getIcon(status()) }}</mat-icon>
      {{ getAbbreviation(status()) }}
    </span>
  `,
  styles: `
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 2px;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }
    .status-badge mat-icon {
      font-size: 14px;
      width: 14px;
      height: 14px;
    }
    .status-pending {
      background: var(--clr-review-pending-bg);
      color: var(--clr-review-pending);
    }
    .status-reviewed {
      background: var(--clr-review-reviewed-bg);
      color: var(--clr-review-reviewed);
    }
    .status-approved {
      background: var(--clr-review-approved-bg);
      color: var(--clr-review-approved);
    }
    .status-flagged {
      background: var(--clr-review-flagged-bg);
      color: var(--clr-review-flagged);
    }
    .status-uncategorized {
      background: var(--clr-uncategorized-bg);
      color: var(--clr-uncategorized);
    }
  `,
})
export class StatusBadgeComponent {
  status = input.required<string>();

  readonly iconMap: Record<string, string> = {
    pending: 'schedule',
    reviewed: 'visibility',
    approved: 'check_circle',
    flagged: 'flag',
    uncategorized: 'label_off',
  };

  readonly abbreviationMap: Record<string, string> = {
    pending: 'P',
    reviewed: 'R',
    approved: 'A',
    flagged: 'F',
    uncategorized: 'SC',
  };

  getIcon(s: string): string {
    return this.iconMap[s] || 'help_outline';
  }

  getAbbreviation(s: string): string {
    return this.abbreviationMap[s] || '?';
  }
}
