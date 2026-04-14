import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-page-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="page-header">
      <div>
        <h1>{{ title() }}</h1>
        @if (subtitle()) {
          <span class="header-subtitle">{{ subtitle() }}</span>
        }
      </div>
      <div class="spacer"></div>
      <ng-content />
    </div>
  `,
  styles: `
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spc-24);
    }
    h1 {
      margin: 0;
      font-size: var(--font-xl);
      font-weight: var(--fw-regular);
      line-height: var(--lh-tight);
      color: var(--clr-text-primary);
    }
    .header-subtitle {
      font-size: var(--font-sm);
      color: var(--clr-text-muted);
    }
    .spacer {
      flex: 1 1 auto;
    }
  `,
})
export class PageHeaderComponent {
  title = input.required<string>();
  subtitle = input<string>();
}
