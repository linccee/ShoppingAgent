import { useCallback } from 'react';

import { useAppDispatch, useAppState } from '../context/useAppStore';
import {
  ApiError,
  createSession,
  deleteSession,
  getHealth,
  getSession,
  listSessions,
} from '../services/api';
import type { SessionSummary } from '../types';
import { logger } from '../utils/logger';

const ACTIVE_SESSION_KEY = 'mirror-curation.active-session-id';

function persistActiveSession(sessionId: string): void {
  window.localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
}

function clearActiveSession(): void {
  window.localStorage.removeItem(ACTIVE_SESSION_KEY);
}

function getPreferredSessionId(sessions: SessionSummary[]): string | null {
  const stored = window.localStorage.getItem(ACTIVE_SESSION_KEY);
  if (stored && sessions.some((session) => session.session_id === stored)) {
    return stored;
  }
  return sessions[0]?.session_id ?? null;
}

export function useSessions() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const refreshSessions = useCallback(async () => {
    logger.debug('Sessions', 'Refreshing sessions');
    const sessions = await listSessions();
    dispatch({ type: 'sessions/set', payload: sessions });
    return sessions;
  }, [dispatch]);

  const loadSession = useCallback(
    async (sessionId: string) => {
      logger.info('Sessions', `Loading session: ${sessionId}`);
      const detail = await getSession(sessionId);
      persistActiveSession(sessionId);
      dispatch({ type: 'session/load', payload: detail });
    },
    [dispatch],
  );

  const createAndSelectSession = useCallback(async () => {
    logger.info('Sessions', 'Creating new session');
    const created = await createSession();
    const detail = await getSession(created.session_id);
    persistActiveSession(created.session_id);
    const sessions = await refreshSessions();

    if (!sessions.some((session) => session.session_id === created.session_id)) {
      dispatch({
        type: 'sessions/set',
        payload: [
          {
            session_id: detail.session_id,
            title: detail.title,
            updated_at: detail.updated_at,
            created_at: detail.created_at,
          },
          ...sessions,
        ],
      });
    }

    dispatch({ type: 'session/create', payload: detail });
  }, [dispatch, refreshSessions]);

  const recoverMissingSession = useCallback(async () => {
    logger.warn('Sessions', 'Recovering missing session');
    clearActiveSession();
    await createAndSelectSession();
  }, [createAndSelectSession]);

  const initializeApp = useCallback(async () => {
    logger.info('Sessions', 'Initializing app');
    try {
      const [healthResult, sessions] = await Promise.all([
        getHealth().catch(() => null),
        listSessions(),
      ]);

      dispatch({
        type: 'health/set',
        payload: {
          health: healthResult ? healthResult.status : 'error',
          runtimeConfig: {
            model: healthResult?.model ?? null,
            temperature: healthResult?.temperature ?? 0,
            max_tokens: healthResult?.max_tokens ?? 0,
            memory_turns: healthResult?.memory_turns ?? 0,
          },
        },
      });
      dispatch({ type: 'sessions/set', payload: sessions });

      const targetSessionId = getPreferredSessionId(sessions);
      if (targetSessionId) {
        try {
          await loadSession(targetSessionId);
        } catch (error) {
          if (error instanceof ApiError && error.status === 404) {
            logger.warn('Sessions', `Session ${targetSessionId} not found, recovering`);
            await recoverMissingSession();
          } else {
            throw error;
          }
        }
      } else {
        await createAndSelectSession();
      }

      dispatch({ type: 'bootstrap/complete' });
    } catch (error) {
      logger.error('Sessions', 'App initialization failed', error instanceof Error ? error.message : 'Unknown error');
      dispatch({
        type: 'bootstrap/error',
        payload: error instanceof Error ? error.message : '初始化失败',
      });
    }
  }, [createAndSelectSession, dispatch, loadSession, recoverMissingSession]);

  const removeSession = useCallback(
    async (sessionId: string) => {
      logger.info('Sessions', `Removing session: ${sessionId}`);
      const removingActive = sessionId === state.activeSessionId;
      const storedSessionId = window.localStorage.getItem(ACTIVE_SESSION_KEY);

      await deleteSession(sessionId);

      if (storedSessionId === sessionId || removingActive) {
        clearActiveSession();
      }

      const sessions = await refreshSessions();

      if (!removingActive) {
        return;
      }

      if (sessions.length === 0) {
        await createAndSelectSession();
        return;
      }

      const nextSessionId = sessions[0].session_id;
      try {
        await loadSession(nextSessionId);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          logger.warn('Sessions', `Next session ${nextSessionId} not found, recovering`);
          await recoverMissingSession();
          return;
        }
        throw error;
      }
    },
    [
      createAndSelectSession,
      loadSession,
      recoverMissingSession,
      refreshSessions,
      state.activeSessionId,
    ],
  );

  const removeActiveSession = useCallback(async () => {
    if (!state.activeSessionId) {
      return;
    }

    await removeSession(state.activeSessionId);
  }, [removeSession, state.activeSessionId]);

  return {
    initializeApp,
    refreshSessions,
    loadSession,
    createAndSelectSession,
    removeSession,
    removeActiveSession,
  };
}
