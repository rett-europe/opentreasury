import {
  ChangeDetectionStrategy, Component, effect, inject, input, output, signal,
} from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AppSettingsService } from '@core/services/app-settings.service';
import { TransactionService } from '@core/services/transaction.service';
import { TransactionNote } from '@shared/models/transaction.model';

@Component({
  selector: 'app-transaction-notes',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatFormFieldModule, MatInputModule, MatButtonModule, MatSnackBarModule],
  template: `
    <div class="notes-section">
      <h3>{{ settings.labels().notesSection }} ({{ notes().length }})</h3>

      @for (note of notes(); track note.id) {
        <div class="note-card">
          <div class="note-meta">
            {{ note.authorName ?? note.author }} &middot; {{ formatDate(note.createdAt) }}
          </div>
          <div class="note-text">{{ note.text }}</div>
        </div>
      }

      <div class="add-note-row">
        <mat-form-field appearance="outline" class="note-input">
          <mat-label>{{ settings.labels().addNotePlaceholder }}</mat-label>
          <textarea matInput [value]="newNoteText()"
                    (input)="newNoteText.set(asInput($event))"
                    rows="2"></textarea>
        </mat-form-field>
        <button mat-flat-button color="primary" type="button"
                [disabled]="!newNoteText().trim() || adding()"
                (click)="addNote()">
          {{ settings.labels().addNote }}
        </button>
      </div>
    </div>
  `,
  styles: `
    .notes-section {
      margin: var(--spc-24) 0 var(--spc-16);
    }
    .notes-section h3 {
      font-size: var(--font-md);
      font-weight: var(--fw-medium);
      color: var(--clr-text-primary);
      margin-bottom: var(--spc-12);
    }
    .note-card {
      background: var(--clr-surface-panel);
      border-radius: var(--rad-md);
      padding: var(--spc-12) var(--spc-16);
      margin-bottom: var(--spc-8);
      border-left: 3px solid var(--brand-primary-light);
    }
    .note-meta {
      font-size: var(--font-sm);
      color: var(--clr-text-muted);
      margin-bottom: var(--spc-4);
    }
    .note-text {
      font-size: var(--font-body);
      color: var(--clr-text-primary);
      line-height: var(--lh-relaxed);
    }
    .add-note-row {
      display: flex;
      gap: var(--spc-12);
      align-items: flex-start;
      margin-top: var(--spc-8);
    }
    .note-input { flex: 1; }
  `,
})
export class TransactionNotesComponent {
  transactionId = input.required<string>();
  year = input.required<number>();
  month = input.required<number>();
  initialNotes = input<TransactionNote[]>([]);

  notesUpdated = output<void>();

  readonly notes = signal<TransactionNote[]>([]);
  readonly newNoteText = signal('');
  readonly adding = signal(false);

  readonly settings = inject(AppSettingsService);
  private readonly transactionService = inject(TransactionService);
  private readonly snackBar = inject(MatSnackBar);

  constructor() {
    effect(() => this.notes.set(this.initialNotes()));
  }

  addNote(): void {
    const text = this.newNoteText().trim();
    if (!text || this.adding()) return;
    this.adding.set(true);
    this.transactionService
      .addNote(this.transactionId(), { text }, this.year(), this.month())
      .subscribe({
        next: (tx) => {
          this.notes.set(
            [...(tx.notes ?? [])].sort(
              (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
            ),
          );
          this.newNoteText.set('');
          this.adding.set(false);
          this.snackBar.open(this.settings.labels().noteAdded, '', { duration: 2500 });
          this.notesUpdated.emit();
        },
        error: () => this.adding.set(false),
      });
  }

  formatDate(iso: string): string {
    const d = new Date(iso);
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  }

  asInput(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }
}
