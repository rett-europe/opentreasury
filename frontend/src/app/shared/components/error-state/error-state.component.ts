import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-error-state',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatIconModule, MatButtonModule],
  template: `
    <div class="error-state">
      <mat-icon>error_outline</mat-icon>
      <p>{{ message() }}</p>
      @if (retryLabel()) {
        <button mat-stroked-button color="primary" (click)="retry.emit()">
          {{ retryLabel() }}
        </button>
      }
    </div>
  `,
  styles: `
    .error-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 48px;
      color: var(--clr-error, currentColor);
    }
    .error-state mat-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      margin-bottom: 16px;
    }
    .error-state p {
      margin: 0 0 16px;
      font-size: 14px;
    }
  `,
})
export class ErrorStateComponent {
  message = input.required<string>();
  retryLabel = input<string>();
  retry = output<void>();
}
