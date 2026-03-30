import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AUTH_SESSION_INVALIDATED_EVENT } from '../utils/auth';
import { ApiError, listSessions } from './api';

function createLocalStorageMock(): Storage {
  const store = new Map<string, string>();

  return {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.get(key) ?? null;
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, value);
    },
  };
}

describe('services/api unauthorized handling', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    const localStorageMock = createLocalStorageMock();
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      configurable: true,
    });
    Object.defineProperty(globalThis, 'localStorage', {
      value: localStorageMock,
      configurable: true,
    });
  });

  it('clears auth state and emits an invalidation event on 401', async () => {
    window.localStorage.setItem('access_token', 'expired-token');
    window.localStorage.setItem('user', JSON.stringify({ id: 'u1', username: 'demo' }));

    const invalidationListener = vi.fn();
    window.addEventListener(AUTH_SESSION_INVALIDATED_EVENT, invalidationListener);

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Token expired' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    await expect(listSessions()).rejects.toMatchObject<ApiError>({
      status: 401,
      message: 'Token expired',
    });

    expect(window.localStorage.getItem('access_token')).toBeNull();
    expect(window.localStorage.getItem('user')).toBeNull();
    expect(invalidationListener).toHaveBeenCalledTimes(1);

    window.removeEventListener(AUTH_SESSION_INVALIDATED_EVENT, invalidationListener);
  });
});
