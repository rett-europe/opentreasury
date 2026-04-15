import { ChangeDetectionStrategy, Component, inject, OnInit, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AppSettingsService } from '@core/services/app-settings.service';
import { CategoryService } from '@core/services/category.service';
import { Category, CATEGORY_TYPES } from '@shared/models/category.model';
import { CategoryFormDialogComponent } from './category-form-dialog.component';
import { LoadingContainerComponent } from '@shared/components/loading-container/loading-container.component';
import { EmptyStateComponent } from '@shared/components/empty-state/empty-state.component';
import { PageHeaderComponent } from '@shared/components/page-header/page-header.component';
import { ConfirmDialogComponent, ConfirmDialogData } from '@shared/components/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-category-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatChipsModule,
    MatDialogModule,
    MatSnackBarModule,
    LoadingContainerComponent,
    EmptyStateComponent,
    PageHeaderComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="settings.labels().categories">
        <button mat-fab extended color="primary" (click)="openForm()">
          <mat-icon>add</mat-icon>
          {{ settings.labels().newCategory }}
        </button>
      </app-page-header>

      <app-loading-container [loading]="loading()">
        <div class="card-grid">
          @for (cat of categories(); track cat.id) {
            <mat-card class="category-card" [class.inactive]="!cat.isActive">
              <mat-card-header>
                <mat-card-title>
                  {{ cat.name }}
                  <span class="category-type-badge"
                        [class.income]="cat.categoryType === CATEGORY_TYPES.INCOME"
                        [class.expense]="cat.categoryType === CATEGORY_TYPES.EXPENSE">
                    {{ cat.categoryType === CATEGORY_TYPES.INCOME ? settings.labels().incomeType : settings.labels().expenseType }}
                  </span>
                  @if (!cat.isActive) {
                    <span class="inactive-badge">{{ settings.labels().inactiveLabel }}</span>
                  }
                </mat-card-title>
              </mat-card-header>
              <mat-card-content>
                @if (cat.description) {
                  <p class="cat-description">{{ cat.description }}</p>
                }
                <div class="subcategory-list">
                  <mat-chip-set>
                    @for (sub of cat.subcategories; track sub.id) {
                      <mat-chip class="sub-chip">{{ sub.name }}</mat-chip>
                    } @empty {
                      <span class="no-subs">{{ settings.labels().noSubcategories }}</span>
                    }
                  </mat-chip-set>
                </div>
              </mat-card-content>
              <mat-card-actions align="end">
                <button mat-icon-button (click)="openForm(cat)">
                  <mat-icon>edit</mat-icon>
                </button>
                <button mat-icon-button color="warn" (click)="deleteCategory(cat)">
                  <mat-icon>delete</mat-icon>
                </button>
              </mat-card-actions>
            </mat-card>
          }
        </div>

        @if (categories().length === 0) {
          <app-empty-state icon="category" [message]="settings.labels().noCategoriesEmpty" />
        }
      </app-loading-container>
    </div>
  `,
  styles: `
    .cat-description {
      color: var(--clr-text-muted);
      font-size: var(--font-sm);
      margin-bottom: var(--spc-12);
    }

    .subcategory-list {
      margin-top: var(--spc-8);
    }

    .sub-chip {
      background: var(--brand-surface) !important;
      color: var(--brand-primary) !important;
      font-size: var(--font-sm);
    }

    .no-subs {
      color: var(--clr-text-disabled);
      font-style: italic;
      font-size: var(--font-sm);
    }

    .category-card {
      background: var(--clr-surface);
      border: 1px solid var(--clr-border);
      border-radius: var(--rad-lg);
      box-shadow: var(--elev-card);
      transition: box-shadow var(--transition-normal);
    }
    .category-card:hover {
      box-shadow: var(--elev-card-hover);
    }
    .category-card.inactive {
      opacity: 0.65;
    }

    .category-type-badge {
      display: inline-block;
      padding: var(--spc-2) var(--spc-10);
      border-radius: var(--rad-lg);
      font-size: var(--font-xs);
      font-weight: var(--fw-medium);
      vertical-align: middle;
      margin-left: var(--spc-8);
    }
    .category-type-badge.income { background: var(--clr-income-bg); color: var(--clr-income); }
    .category-type-badge.expense { background: var(--clr-expense-bg); color: var(--clr-expense); }

    .inactive-badge {
      display: inline-block;
      padding: var(--spc-2) var(--spc-8);
      border-radius: var(--rad-lg);
      font-size: var(--font-xs);
      font-weight: var(--fw-medium);
      background: var(--clr-uncategorized-bg);
      color: var(--clr-text-disabled);
      vertical-align: middle;
      margin-left: var(--spc-6);
      text-decoration: line-through;
    }
  `,
})
export class CategoryListComponent implements OnInit {
  readonly CATEGORY_TYPES = CATEGORY_TYPES;
  private readonly categoryService = inject(CategoryService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  readonly settings = inject(AppSettingsService);

  readonly loading = signal(true);
  readonly categories = signal<Category[]>([]);

  ngOnInit(): void {
    this.loadCategories();
  }

  loadCategories(): void {
    this.loading.set(true);
    this.categoryService.list().subscribe({
      next: (data) => {
        this.categories.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.categories.set([]);
        this.loading.set(false);
      },
    });
  }

  openForm(category?: Category): void {
    const dialogRef = this.dialog.open(CategoryFormDialogComponent, {
      width: '600px',
      maxHeight: '90vh',
      data: category ?? null,
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) this.loadCategories();
    });
  }

  deleteCategory(category: Category): void {
    const labels = this.settings.labels();
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: labels.editCategory,
        message: labels.deleteCategoryConfirm(category.name),
        confirmLabel: labels.save,
        color: 'warn',
      } satisfies ConfirmDialogData,
    });
    dialogRef.afterClosed().subscribe((confirmed) => {
      if (!confirmed) return;
      this.categoryService.delete(category.id).subscribe({
        next: () => {
          this.snackBar.open(`${category.name}`, labels.close, { duration: 3000 });
          this.loadCategories();
        },
        error: (err) => {
          const detail = err?.error?.detail || labels.categorySaveError;
          this.snackBar.open(detail, labels.close, { duration: 5000 });
        },
      });
    });
  }
}
