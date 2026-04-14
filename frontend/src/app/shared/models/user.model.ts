export type UserRole = 'Admin' | 'Viewer';

export interface UserProfile {
  id: string;
  displayName: string;
  email: string;
  role: UserRole;
}

export interface UserPreferences {
  language: string;
  theme: string;
  compactMode: boolean;
  reducedMotion: boolean;
}
