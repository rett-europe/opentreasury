import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { AppSettingsService } from '@core/services/app-settings.service';
import { TagService } from '@core/services/tag.service';
import { ReferenceDataService } from '@core/services/reference-data.service';
import { Tag } from '@shared/models/tag.model';
import { TagFormDialogComponent } from './tag-form-dialog.component';
import { LoadingContainerComponent } from '@shared/components/loading-container/loading-container.component';
import { EmptyStateComponent } from '@shared/components/empty-state/empty-state.component';
import { PageHeaderComponent } from '@shared/components/page-header/page-header.component';
import { ConfirmDialogComponent, ConfirmDialogData } from '@shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-tag-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatDialogModule,
    MatSlideToggleModule,
    LoadingContainerComponent,
    EmptyStateComponent,
    PageHeaderComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="settings.labels().tags">
        <button mat-fab extended color="primary" (click)="openForm()">
          <mat-icon>add</mat-icon>
          {{ settings.labels().newTag }}
        </button>
      </app-page-header>

      <app-loading-container [loading]="loading()">
        <div class="tag-grid">
          @for (tag of tags(); track tag.id) {
            <div class="tag-card" [class.inactive]="!tag.isActive">
              <div class="tag-chip-preview"
                   [style.background-color]="tag.color"
                   [style.color]="refData.contrastColor(tag.color)">
                @if (!tag.isActive) {
                  <span class="tag-name-inactive">{{ tag.name }}</span>
                } @else {
                  {{ tag.name }}
                }
              </div>
              @if (!tag.isActive) {
                <span class="inactive-label">{{ settings.labels().inactiveLabel }}</span>
              }
              <div class="tag-actions">
                <mat-slide-toggle
                  [checked]="tag.isActive"
                  (change)="toggleActive(tag)"
                  size="small">
                </mat-slide-toggle>
                <button mat-icon-button (click)="openForm(tag)">
                  <mat-icon>edit</mat-icon>
                </button>
                <button mat-icon-button color="warn" (click)="deleteTag(tag)">
                  <mat-icon>delete</mat-icon>
                </button>
              </div>
            </div>
          }
        </div>

        @if (tags().length === 0) {
          <app-empty-state icon="label" [message]="settings.labels().noTagsEmpty" />
        }
      </app-loading-container>
    </div>
  `,
  styles: `
    .tag-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: var(--spc-16);
    }

    .tag-card {
      background: var(--clr-surface);
      border: 1px solid var(--clr-border);
      border-radius: var(--rad-lg);
      padding: var(--spc-16);
      display: flex;
      flex-direction: column;
      gap: var(--spc-8);
      box-shadow: var(--elev-card);
      transition: box-shadow var(--transition-normal);
    }
    .tag-card:hover {
      box-shadow: var(--elev-card-hover);
    }

    .tag-card.inactive {
      background: var(--clr-surface-panel);
      border-style: dashed;
    }

    .tag-chip-preview {
      display: inline-block;
      padding: var(--spc-4) var(--spc-12);
      border-radius: var(--rad-pill);
      font-size: var(--font-body);
      font-weight: var(--fw-medium);
      width: fit-content;
    }
    .tag-name-inactive {
      text-decoration: line-through;
    }

    .inactive-label {
      font-size: var(--font-xs);
      color: var(--clr-text-disabled);
      font-weight: var(--fw-medium);
      text-transform: uppercase;
      letter-spacing: var(--ls-section);
    }

    .tag-actions {
      display: flex;
      align-items: center;
      gap: var(--spc-4);
      margin-top: var(--spc-4);
    }
  `,
})
export class TagListComponent implements OnInit {
  private readonly tagService = inject(TagService);
  readonly refData = inject(ReferenceDataService);
  private readonly dialog = inject(MatDialog);
  readonly settings = inject(AppSettingsService);

  readonly loading = signal(true);
  readonly tags = signal<Tag[]>([]);

  ngOnInit(): void {
    this.loadTags();
  }

  loadTags(): void {
    this.loading.set(true);
    this.tagService.list().subscribe({
      next: (data) => {
        this.tags.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.tags.set([]);
        this.loading.set(false);
      },
    });
  }

  openForm(tag?: Tag): void {
    const dialogRef = this.dialog.open(TagFormDialogComponent, {
      width: '480px',
      maxHeight: '90vh',
      data: tag ?? null,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.loadTags();
        this.refData.invalidate();
      }
    });
  }

  toggleActive(tag: Tag): void {
    this.tagService.update(tag.id, { isActive: !tag.isActive }).subscribe({
      next: () => {
        this.loadTags();
        this.refData.invalidate();
      },
    });
  }

  deleteTag(tag: Tag): void {
    const labels = this.settings.labels();
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: labels.editTag,
        message: labels.deleteTagConfirm(tag.name),
        color: 'warn',
      } satisfies ConfirmDialogData,
    });
    dialogRef.afterClosed().subscribe((confirmed) => {
      if (!confirmed) return;
      this.tagService.delete(tag.id).subscribe({
        next: () => {
          this.loadTags();
          this.refData.invalidate();
        },
      });
    });
  }
}
