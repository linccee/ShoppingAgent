export const AUTH_SESSION_INVALIDATED_EVENT = 'auth:session-invalidated';

export type AuthInvalidationReason = 'invalid_storage' | 'logout' | 'unauthorized';

export function clearStoredAuthSession(): void {
  window.localStorage.removeItem('access_token');
  window.localStorage.removeItem('user');
}

export function invalidateAuthSession(reason: AuthInvalidationReason): void {
  clearStoredAuthSession();
  window.dispatchEvent(
    new CustomEvent<AuthInvalidationReason>(AUTH_SESSION_INVALIDATED_EVENT, {
      detail: reason,
    }),
  );
}
