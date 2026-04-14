import { ChangeDetectionStrategy, Component, inject, input } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { AppSettingsService } from '@core/services/app-settings.service';
import { KpiCardComponent } from '@shared/components/kpi-card/kpi-card.component';
import { TransactionSummary } from '@shared/models/report.model';

@Component({
  selector: 'app-kpi-strip',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [KpiCardComponent, CurrencyPipe],
  template: `
    <div class="kpi-strip">
      <app-kpi-card
        icon="trending_up"
        [label]="settings.labels().totalIncome"
        [value]="(summary()?.totalIncome ?? 0 | currency: 'EUR':'symbol':'1.2-2') ?? ''"
        colorClass="income" />
      <app-kpi-card
        icon="trending_down"
        [label]="settings.labels().totalExpenses"
        [value]="(summary()?.totalExpenses ?? 0 | currency: 'EUR':'symbol':'1.2-2') ?? ''"
        colorClass="expense" />
      <app-kpi-card
        icon="account_balance_wallet"
        [label]="settings.labels().totalNet"
        [value]="(summary()?.net ?? 0 | currency: 'EUR':'symbol':'1.2-2') ?? ''"
        colorClass="net" />
    </div>
  `,
  styles: `
    .kpi-strip {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: var(--spc-16);
    }
  `,
})
export class KpiStripComponent {
  readonly settings = inject(AppSettingsService);
  summary = input.required<TransactionSummary | null>();
}
