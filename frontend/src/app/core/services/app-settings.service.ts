import { DOCUMENT } from '@angular/common';
import { DestroyRef, Injectable, computed, effect, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, catchError, debounceTime, filter, of, switchMap, take } from 'rxjs';
import { toObservable } from '@angular/core/rxjs-interop';
import { AppLabels } from '../i18n/labels.type';
import { ES_LABELS } from '../i18n/es';
import { EN_LABELS } from '../i18n/en';
import { AuthService } from '../auth/auth.service';
import { UserService } from './user.service';

type AppLanguage = 'es' | 'en';
type ThemeMode = 'light' | 'dark';

interface AppSettings {
  language: AppLanguage;
  theme: ThemeMode;
  compactMode: boolean;
  reducedMotion: boolean;
}

const STORAGE_KEY = 'opentreasury.app-settings';

const DEFAULT_SETTINGS: AppSettings = {
  language: 'es',
  theme: 'light',
  compactMode: false,
  reducedMotion: false,
};

const LABELS: Record<AppLanguage, AppLabels> = {
  es: ES_LABELS,
  en: EN_LABELS,
};

@Injectable({ providedIn: 'root' })
export class AppSettingsService {
  private readonly document = inject(DOCUMENT);
  private readonly authService = inject(AuthService);
  private readonly userService = inject(UserService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly state = signal<AppSettings>(this.loadSettings());

  /** Emits whenever the user explicitly changes a preference. */
  private readonly save$ = new Subject<AppSettings>();

  /**
   * Tracks whether the user has changed any setting since the page loaded.
   * Prevents a slow server response from overwriting in-flight user changes.
   */
  private _userModified = false;

  readonly language = computed(() => this.state().language);
  readonly theme = computed(() => this.state().theme);
  readonly compactMode = computed(() => this.state().compactMode);
  readonly reducedMotion = computed(() => this.state().reducedMotion);
  readonly labels = computed(() => LABELS[this.language()]);

  constructor() {
    // Apply + locally persist on every change.
    effect(() => {
      const settings = this.state();
      this.persistSettings(settings);
      this.applySettings(settings);
    });

    // Debounce and persist to the server; only when authenticated.
    this.save$
      .pipe(
        filter(() => this.authService.isAuthenticated()),
        debounceTime(500),
        switchMap((s) => this.userService.savePreferences(s).pipe(catchError(() => of(null)))),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe();

    // Load server-side preferences only after the user is authenticated,
    // to avoid triggering MSAL redirect before login completes.
    toObservable(this.authService.isAuthenticated)
      .pipe(
        filter((authed) => authed),
        take(1),
        switchMap(() => this.userService.getPreferences()),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (prefs) => {
          if (this._userModified) {
            return;
          }
          this.state.set({
            language: (prefs.language as AppLanguage) ?? DEFAULT_SETTINGS.language,
            theme: (prefs.theme as ThemeMode) ?? DEFAULT_SETTINGS.theme,
            compactMode: prefs.compactMode ?? DEFAULT_SETTINGS.compactMode,
            reducedMotion: prefs.reducedMotion ?? DEFAULT_SETTINGS.reducedMotion,
          });
        },
        error: () => {
          // Server unavailable — keep localStorage values.
        },
      });
  }

  setLanguage(language: AppLanguage): void {
    this.updateSettings({ language });
  }

  setTheme(theme: ThemeMode): void {
    this.updateSettings({ theme });
  }

  setCompactMode(compactMode: boolean): void {
    this.updateSettings({ compactMode });
  }

  setReducedMotion(reducedMotion: boolean): void {
    this.updateSettings({ reducedMotion });
  }

  private updateSettings(patch: Partial<AppSettings>): void {
    this._userModified = true;
    this.state.update((current) => ({ ...current, ...patch }));
    this.save$.next(this.state());
  }

  private loadSettings(): AppSettings {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return DEFAULT_SETTINGS;
      }

      return { ...DEFAULT_SETTINGS, ...(JSON.parse(raw) as Partial<AppSettings>) };
    } catch {
      return DEFAULT_SETTINGS;
    }
  }

  private persistSettings(settings: AppSettings): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }

  private applySettings(settings: AppSettings): void {
    const body = this.document.body;
    const html = this.document.documentElement;

    body.classList.toggle('theme-dark', settings.theme === 'dark');
    body.classList.toggle('theme-light', settings.theme === 'light');
    body.classList.toggle('density-compact', settings.compactMode);
    body.classList.toggle('reduced-motion', settings.reducedMotion);

    html.lang = settings.language;
    html.style.colorScheme = settings.theme;
  }
}
