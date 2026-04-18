import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { ReferenceDataService } from '@core/services/reference-data.service';

/**
 * Renders a bank account as a colored label/chip. The background uses the
 * account's assigned color (issue #20); when no color is set, falls back to
 * the theme's neutral surface. Dark text (#1f2937) is used on soft pastel
 * backgrounds to guarantee WCAG AA contrast.
 */
@Component({
  selector: 'app-account-label',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="account-label"
          [style.background-color]="color() || null"
          [class.no-color]="!color()">
      {{ label() }}
    </span>
  `,
  styles: `
    .account-label {
      display: inline-block;
      padding: 2px 8px;
      border-radius: var(--rad-pill, 12px);
      font-size: var(--font-xs, 11px);
      font-weight: var(--fw-semibold, 600);
      line-height: 1.4;
      color: #1f2937;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      vertical-align: middle;
    }
    .account-label.no-color {
      background: var(--clr-uncategorized-bg, #e0e0e0);
      color: var(--clr-text-secondary, #374151);
    }
  `,
})
export class AccountLabelComponent {
  private readonly refData = inject(ReferenceDataService);

  accountId = input.required<string>();

  readonly label = computed(() => this.refData.getAccountLabel(this.accountId()));
  readonly color = computed(() => this.refData.getAccountColor(this.accountId()));
}
