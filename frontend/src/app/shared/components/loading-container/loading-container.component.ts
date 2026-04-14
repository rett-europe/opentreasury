import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-loading-container',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatProgressSpinnerModule],
  template: `
    @if (loading()) {
      <div class="loading-container">
        <mat-spinner diameter="44" />
      </div>
    } @else {
      <ng-content />
    }
  `,
  styles: `
    .loading-container {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: var(--spc-48);
    }
  `,
})
export class LoadingContainerComponent {
  loading = input.required<boolean>();
}
