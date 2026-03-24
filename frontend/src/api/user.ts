import api from './client';

export type LanguagePreference = 'auto' | 'zh-CN' | 'en-US';

export interface UserPreferences {
  default_currency: string;
  favorite_platforms: string[];
  budget_range: { min: number; max: number };
  notification_enabled: boolean;
  language_preference: LanguagePreference;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  created_at: string | null;
  last_login: string | null;
  is_active: boolean;
  role: string;
  preferences: UserPreferences;
}

export const userApi = {
  getCurrentUser: () =>
    api.get<UserResponse>('/users/me'),

  updateUser: (username?: string, email?: string) =>
    api.put<{ message: string }>('/users/me', { username, email }),

  updatePreferences: (preferences: UserPreferences) =>
    api.put<{ message: string }>('/users/me/preferences', preferences),

  deleteAccount: () =>
    api.delete('/users/me'),
};
