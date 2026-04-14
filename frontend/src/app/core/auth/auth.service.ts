import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MsalService } from '@azure/msal-angular';
import { AccountInfo } from '@azure/msal-browser';
import { environment } from '@env/environment';
import { UserProfile, UserRole } from '@shared/models/user.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly msalService = inject(MsalService);
  private readonly http = inject(HttpClient);

  private readonly _account = signal<AccountInfo | null>(null);
  private readonly _role = signal<UserRole>('Viewer');
  private readonly _profileLoaded = signal(false);

  readonly isAuthenticated = computed(() => this._account() !== null);
  readonly account = this._account.asReadonly();
  readonly displayName = computed(() => this._account()?.name ?? '');
  readonly role = this._role.asReadonly();
  readonly isAdmin = computed(() => this._role() === 'Admin');
  readonly profileLoaded = this._profileLoaded.asReadonly();

  initialize(): void {
    this.msalService.handleRedirectObservable().subscribe(() => {
      this.checkAccount();
    });
  }

  checkAccount(): void {
    const accounts = this.msalService.instance.getAllAccounts();
    const account = accounts.length > 0 ? accounts[0] : null;
    this._account.set(account);
    if (account && !this._profileLoaded()) {
      this.loadProfile();
    }
  }

  private loadProfile(): void {
    this.http.get<UserProfile>(`${environment.apiBaseUrl}/me`).subscribe({
      next: (profile) => {
        this._role.set(profile.role);
        this._profileLoaded.set(true);
      },
      error: () => {
        // Default to Viewer on error for safety
        this._role.set('Viewer');
        this._profileLoaded.set(true);
      },
    });
  }

  login(): void {
    this.msalService.loginRedirect();
  }

  logout(): void {
    this.msalService.logoutRedirect();
  }
}
