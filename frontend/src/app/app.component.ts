import { ChangeDetectionStrategy, Component, OnInit, ViewChild, inject, signal } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { MatBadgeModule } from '@angular/material/badge';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSidenav, MatSidenavModule } from '@angular/material/sidenav';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MsalBroadcastService } from '@azure/msal-angular';
import { InteractionStatus } from '@azure/msal-browser';
import { filter } from 'rxjs';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './core/auth/auth.service';
import { AppSettingsService } from './core/services/app-settings.service';
import { ReferenceDataService } from './core/services/reference-data.service';

@Component({
  selector: 'app-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatBadgeModule,
    MatButtonToggleModule,
    MatSlideToggleModule,
    MatDividerModule,
  ],
  template: `
    <!-- ═══ Toolbar ═══ -->
    <header class="app-toolbar">
      <button mat-icon-button (click)="sidenav.toggle()" [attr.aria-label]="settings.labels().menu">
        <mat-icon>menu</mat-icon>
      </button>

      <div class="toolbar-brand">
        <span class="brand-mark">✦</span>
        <span class="brand-title">OpenTreasury</span>
      </div>

      <span class="spacer"></span>

      <button
        mat-icon-button
        class="settings-trigger"
        (click)="settingsSidenav.toggle()"
        [attr.aria-label]="settings.labels().openSettings"
      >
        <mat-icon>tune</mat-icon>
      </button>
    </header>

    <!-- ═══ Layout ═══ -->
    <mat-sidenav-container class="app-container">

      <!-- ─── Left sidenav ─── -->
      <mat-sidenav
        #sidenav
        [mode]="isMobile() ? 'over' : 'side'"
        [opened]="!isMobile()"
        class="app-sidenav"
      >
        <nav class="nav-list" aria-label="Main navigation">
          <div class="nav-section-label">{{ settings.labels().sectionMain }}</div>

          <a class="nav-item" routerLink="/dashboard" routerLinkActive="active" (click)="closeMobileNav()">
            <mat-icon>dashboard</mat-icon>
            <span>{{ settings.labels().dashboard }}</span>
          </a>

          <a class="nav-item" routerLink="/transactions" routerLinkActive="active" (click)="closeMobileNav()">
            <mat-icon>receipt_long</mat-icon>
            <span>{{ settings.labels().transactions }}</span>
          </a>

          <a class="nav-item" routerLink="/balance" routerLinkActive="active" (click)="closeMobileNav()">
            <mat-icon>balance_scale</mat-icon>
            <span>{{ settings.labels().balance }}</span>
          </a>

          @if (authService.isAdmin()) {
            <div class="nav-section-label">{{ settings.labels().sectionConfig }}</div>

            <a class="nav-item" routerLink="/categories" routerLinkActive="active" (click)="closeMobileNav()">
              <mat-icon>category</mat-icon>
              <span>{{ settings.labels().categories }}</span>
            </a>

            <a class="nav-item" routerLink="/tags" routerLinkActive="active" (click)="closeMobileNav()">
              <mat-icon>label</mat-icon>
              <span>{{ settings.labels().tags }}</span>
            </a>

            <a class="nav-item" routerLink="/accounts" routerLinkActive="active" (click)="closeMobileNav()">
              <mat-icon>account_balance</mat-icon>
              <span>{{ settings.labels().accounts }}</span>
            </a>
          }

          <div class="nav-section-label">{{ settings.labels().sectionData }}</div>

          @if (authService.isAdmin()) {
            <a class="nav-item" routerLink="/import" routerLinkActive="active" (click)="closeMobileNav()">
              <mat-icon>upload_file</mat-icon>
              <span>{{ settings.labels().import }}</span>
            </a>
          }

          <a class="nav-item" routerLink="/export" routerLinkActive="active" (click)="closeMobileNav()">
            <mat-icon>download</mat-icon>
            <span>{{ settings.labels().export }}</span>
          </a>
        </nav>

        <!-- User footer -->
        @if (authService.isAuthenticated()) {
          <div class="sidenav-footer">
            <div class="user-info">
              <mat-icon class="user-avatar">person</mat-icon>
              <div class="user-details">
                <span class="user-name">{{ authService.displayName() }}</span>
                <span class="user-role" [class.admin]="authService.isAdmin()">
                  {{ authService.role() }}
                </span>
              </div>
            </div>
            <button mat-icon-button (click)="authService.logout()" [attr.aria-label]="settings.labels().logout">
              <mat-icon>logout</mat-icon>
            </button>
          </div>
        }
      </mat-sidenav>

      <!-- ─── Right sidenav (settings) ─── -->
      <mat-sidenav
        #settingsSidenav
        position="end"
        [mode]="isMobile() ? 'over' : 'side'"
        [opened]="false"
        class="settings-sidenav"
      >
        <div class="settings-panel">
          <div class="settings-header">
            <div>
              <h2>{{ settings.labels().settingsTitle }}</h2>
              <p>{{ settings.labels().settingsSubtitle }}</p>
            </div>
            <button
              mat-icon-button
              (click)="settingsSidenav.close()"
              [attr.aria-label]="settings.labels().close"
            >
              <mat-icon>close</mat-icon>
            </button>
          </div>

          <mat-divider />

          <section class="settings-section">
            <span class="settings-label">{{ settings.labels().language }}</span>
            <mat-button-toggle-group
              class="full-width-toggle"
              [value]="settings.language()"
              (change)="settings.setLanguage($event.value)"
            >
              <mat-button-toggle value="es">{{ settings.labels().spanish }}</mat-button-toggle>
              <mat-button-toggle value="en">{{ settings.labels().english }}</mat-button-toggle>
            </mat-button-toggle-group>
          </section>

          <section class="settings-section">
            <span class="settings-label">{{ settings.labels().appearance }}</span>
            <mat-button-toggle-group
              class="full-width-toggle"
              [value]="settings.theme()"
              (change)="settings.setTheme($event.value)"
            >
              <mat-button-toggle value="light">{{ settings.labels().light }}</mat-button-toggle>
              <mat-button-toggle value="dark">{{ settings.labels().dark }}</mat-button-toggle>
            </mat-button-toggle-group>
          </section>

          <section class="settings-section">
            <mat-slide-toggle
              [checked]="settings.compactMode()"
              (change)="settings.setCompactMode($event.checked)"
            >
              {{ settings.labels().compactMode }}
            </mat-slide-toggle>
            <p class="settings-hint">{{ settings.labels().compactModeHint }}</p>
          </section>

          <section class="settings-section">
            <mat-slide-toggle
              [checked]="settings.reducedMotion()"
              (change)="settings.setReducedMotion($event.checked)"
            >
              {{ settings.labels().reducedMotion }}
            </mat-slide-toggle>
            <p class="settings-hint">{{ settings.labels().reducedMotionHint }}</p>
          </section>

          <div class="settings-footer-note">
            <mat-icon>tune</mat-icon>
            <span>{{ settings.labels().moreSoon }}</span>
          </div>
        </div>
      </mat-sidenav>

      <!-- ─── Main content ─── -->
      <mat-sidenav-content class="app-content">
        <router-outlet />
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: `
    /* ════ Toolbar ════ */
    .app-toolbar {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: var(--z-toolbar);
      display: flex;
      align-items: center;
      gap: var(--spc-8);
      height: var(--spc-64);
      padding: 0 var(--spc-16);
      background: var(--brand-primary);
      color: var(--brand-on-primary);
    }

    .toolbar-brand {
      display: flex;
      align-items: baseline;
      gap: var(--spc-8);
    }

    .brand-mark {
      font-size: var(--font-lg);
      font-weight: var(--fw-bold);
      line-height: 1;
    }

    .brand-title {
      font-size: var(--font-lg);
      font-weight: var(--fw-semibold);
      line-height: 1;
    }

    .brand-subtitle {
      font-size: var(--font-sm);
      font-weight: var(--fw-medium);
      opacity: 0.72;
      line-height: 1;
    }

    .settings-trigger {
      border: 1px solid rgba(255, 255, 255, 0.18);
      border-radius: var(--rad-md);
      transition: background var(--transition-fast);
    }

    .settings-trigger:hover {
      background: rgba(255, 255, 255, 0.12);
    }

    .spacer {
      flex: 1 1 auto;
    }

    /* ════ Layout shell ════ */
    .app-container {
      position: absolute;
      top: var(--spc-64);
      right: 0;
      bottom: 0;
      left: 0;
    }

    /* ════ Left sidenav ════ */
    .app-sidenav {
      width: 260px;
      display: flex;
      flex-direction: column;
      background: var(--clr-surface);
      border-right: 1px solid var(--clr-border);
    }

    /* ── Nav sections ── */
    .nav-list {
      flex: 1;
      padding: var(--spc-4) var(--spc-12);
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .nav-section-label {
      padding: var(--spc-16) var(--spc-12) var(--spc-6);
      font-size: 11px;
      font-weight: var(--fw-bold);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--clr-text-muted);
      user-select: none;
    }

    .nav-section-label:first-child {
      padding-top: var(--spc-4);
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: var(--spc-12);
      padding: var(--spc-10) var(--spc-12);
      border-radius: var(--rad-sm);
      text-decoration: none;
      cursor: pointer;
      transition: background-color var(--transition-fast);
      border-left: 3px solid transparent;
    }

    .nav-item mat-icon {
      font-size: 20px;
      width: 20px;
      height: 20px;
      color: var(--clr-text-muted);
      flex-shrink: 0;
    }

    .nav-item span {
      font-size: 14px;
      font-weight: var(--fw-normal);
      color: var(--clr-text-secondary);
      line-height: 20px;
    }

    .nav-item:hover {
      background-color: var(--brand-surface-hover);
    }

    .nav-item:hover mat-icon {
      color: var(--brand-primary-light);
    }

    .nav-item:hover span {
      color: var(--clr-text-primary);
    }

    .nav-item.active {
      background-color: var(--brand-surface);
      border-left-color: var(--brand-primary);
    }

    .nav-item.active mat-icon {
      color: var(--brand-primary);
    }

    .nav-item.active span {
      color: var(--brand-primary);
      font-weight: var(--fw-semibold);
    }

    /* ── User footer ── */
    .sidenav-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--spc-16) var(--spc-20);
      border-top: 1px solid var(--clr-divider);
      background: var(--clr-surface-panel);
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: var(--spc-10);
    }

    .user-avatar {
      color: var(--brand-primary-muted);
      font-size: 28px;
      width: 28px;
      height: 28px;
    }

    .user-details {
      display: flex;
      flex-direction: column;
    }

    .user-name {
      font-size: var(--font-sm);
      font-weight: var(--fw-medium);
      color: var(--clr-text-primary);
    }

    .user-role {
      font-size: var(--font-xs);
      font-weight: var(--fw-medium);
      color: var(--clr-text-muted);
      text-transform: uppercase;
      letter-spacing: var(--ls-section);
    }

    .user-role.admin {
      color: var(--brand-primary);
    }

    /* ════ Settings sidenav ════ */
    .settings-sidenav {
      width: min(360px, 100vw);
      border-left: 1px solid var(--clr-border);
    }

    .settings-panel {
      height: 100%;
      display: flex;
      flex-direction: column;
      gap: var(--spc-20);
      padding: var(--spc-24);
      background: var(--clr-surface-panel);
    }

    .settings-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--spc-12);
    }

    .settings-header h2 {
      margin: 0;
      font-size: var(--font-lg);
      font-weight: var(--fw-semibold);
      color: var(--clr-text-primary);
    }

    .settings-header p {
      margin: var(--spc-6) 0 0;
      color: var(--clr-text-muted);
      font-size: var(--font-body);
      line-height: var(--lh-normal);
    }

    .settings-section {
      display: flex;
      flex-direction: column;
      gap: var(--spc-10);
    }

    .settings-label {
      font-size: var(--font-sm);
      font-weight: var(--fw-bold);
      letter-spacing: var(--ls-section);
      text-transform: uppercase;
      color: var(--clr-text-muted);
    }

    .full-width-toggle {
      width: 100%;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
    }

    .full-width-toggle mat-button-toggle {
      width: 100%;
    }

    .settings-hint {
      margin: 0;
      color: var(--clr-text-muted);
      font-size: var(--font-body);
      line-height: var(--lh-normal);
    }

    .settings-footer-note {
      margin-top: auto;
      display: flex;
      align-items: center;
      gap: var(--spc-10);
      padding: var(--spc-12) var(--spc-16);
      border-radius: var(--rad-pill);
      background: var(--brand-surface);
      color: var(--clr-text-muted);
      font-size: var(--font-body);
    }

    /* ════ Main content ════ */
    .app-content {
      padding: var(--spc-24);
    }

    /* ════ Mobile ════ */
    @media (max-width: 767px) {
      .brand-subtitle {
        display: none;
      }

      .sidenav-brand {
        display: none;
      }

      .settings-sidenav {
        width: min(320px, 92vw);
      }

      .app-content {
        padding: var(--spc-16);
      }
    }
  `,
})
export class AppComponent implements OnInit {
  readonly authService = inject(AuthService);
  readonly router = inject(Router);
  readonly settings = inject(AppSettingsService);
  private readonly broadcastService = inject(MsalBroadcastService);
  private readonly refData = inject(ReferenceDataService);
  private readonly breakpointObserver = inject(BreakpointObserver);

  @ViewChild('sidenav') sidenav!: MatSidenav;
  @ViewChild('settingsSidenav') settingsSidenav!: MatSidenav;
  readonly isMobile = signal(false);

  ngOnInit(): void {
    this.authService.initialize();

    this.broadcastService.inProgress$
      .pipe(filter((status) => status === InteractionStatus.None))
      .subscribe(() => {
        this.authService.checkAccount();
        if (this.authService.isAuthenticated()) {
          this.refData.load();
        }
      });

    this.breakpointObserver.observe([Breakpoints.Handset]).subscribe((result) => {
      this.isMobile.set(result.matches);
    });
  }

  closeMobileNav(): void {
    if (this.isMobile()) {
      this.sidenav.close();
    }
  }
}
