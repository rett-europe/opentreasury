import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { UserPreferences, UserProfile } from '@shared/models/user.model';

@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly api = inject(ApiService);

  /** GET /api/me — current user profile + role */
  getProfile(): Observable<UserProfile> {
    return this.api.get<UserProfile>('/me');
  }

  /** GET /api/me/preferences — user's persisted preferences */
  getPreferences(): Observable<UserPreferences> {
    return this.api.get<UserPreferences>('/me/preferences');
  }

  /** PUT /api/me/preferences — persist user preferences */
  savePreferences(prefs: UserPreferences): Observable<UserPreferences> {
    return this.api.put<UserPreferences>('/me/preferences', prefs);
  }
}
