import { ChangeDetectionStrategy, Component, input } from '@angular/core';

@Component({
  selector: 'app-section-title',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="section-title">
      <span>{{ text() }}</span>
      <ng-content />
    </div>
  `,
  styles: `
    .section-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: var(--font-xs);
      font-weight: var(--fw-bold);
      text-transform: uppercase;
      letter-spacing: var(--ls-section);
      margin: var(--spc-24) 0 var(--spc-12);
      color: var(--clr-text-muted);
    }
  `,
})
export class SectionTitleComponent {
  text = input.required<string>();
}
