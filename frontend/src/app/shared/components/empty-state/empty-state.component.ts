import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatIconModule, MatButtonModule],
  template: `
    <div class="empty-state">
      <mat-icon>{{ icon() }}</mat-icon>
      <p>{{ message() }}</p>
      @if (actionLabel()) {
        <button mat-stroked-button (click)="action.emit()">
          {{ actionLabel() }}
        </button>
      }
    </div>
  `,
  styles: `
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: var(--spc-48);
      color: var(--clr-text-muted);
    }
    .empty-state mat-icon {
      font-size: var(--spc-48);
      width: var(--spc-48);
      height: var(--spc-48);
      margin-bottom: var(--spc-16);
      opacity: 0.6;
    }
    .empty-state p {
      margin: 0 0 var(--spc-16);
      font-size: var(--font-body);
    }
  `,
})
export class EmptyStateComponent {
  icon = input.required<string>();
  message = input.required<string>();
  actionLabel = input<string>();
  action = output<void>();
}
