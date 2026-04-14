import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { AppSettingsService } from '@core/services/app-settings.service';

@Component({
  selector: 'app-type-indicator',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (config(); as c) {
      <div class="type-indicator" [class]="c.cssClass">
        {{ c.text }}
      </div>
    }
  `,
  styles: `
    .type-indicator {
      padding: var(--spc-10) var(--spc-16);
      border-radius: var(--rad-sm);
      font-size: var(--font-body);
      font-weight: var(--fw-medium);
      margin: var(--spc-4) 0 var(--spc-16) 0;
      text-align: center;
      transition: background-color var(--transition-normal), color var(--transition-normal);
    }
    .type-income {
      background: var(--clr-income-bg);
      color: var(--clr-income-on-bg);
      border-left: 3px solid var(--clr-income);
    }
    .type-expense {
      background: var(--clr-expense-bg);
      color: var(--clr-expense-on-bg);
      border-left: 3px solid var(--clr-expense);
    }
    .type-transfer {
      background: var(--clr-transfer-bg);
      color: var(--clr-transfer-on-bg);
      border-left: 3px solid var(--clr-transfer);
    }
    .type-refund {
      background: var(--clr-refund-bg);
      color: var(--clr-refund-on-bg);
      border-left: 3px solid var(--clr-refund);
    }
  `,
})
export class TypeIndicatorComponent {
  typeDisplay = input.required<string>();

  private readonly settings = inject(AppSettingsService);

  readonly config = computed(() => {
    const type = this.typeDisplay();
    if (!type) return null;
    const l = this.settings.labels();
    const map: Record<string, { text: string; cssClass: string }> = {
      income:          { text: l.incomeIndicatorV2,      cssClass: 'type-income' },
      expense:         { text: l.expenseIndicatorV2,     cssClass: 'type-expense' },
      transfer_in:     { text: l.transferInIndicator,    cssClass: 'type-transfer' },
      transfer_out:    { text: l.transferOutIndicator,   cssClass: 'type-transfer' },
      refund_received: { text: l.refundReceivedIndicator, cssClass: 'type-refund' },
      refund_given:    { text: l.refundGivenIndicator,   cssClass: 'type-refund' },
    };
    return map[type] ?? null;
  });
}
