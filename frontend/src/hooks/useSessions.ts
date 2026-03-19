import { useCallback } from 'react';

import { useAppDispatch, useAppState } from '../context/useAppStore';
import { createSession, deleteSession, getHealth, getSession, listSessions } from '../services/api';
import type { SessionSummary } from '../types';

const ACTIVE_SESSION_KEY = 'mirror-curation.active-session-id';

function persistActiveSession(sessionId: string): void {
  window.localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
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
    const sessions = await listSessions();
    dispatch({ type: 'sessions/set', payload: sessions });
    return sessions;
  }, [dispatch]);

  const loadSession = useCallback(
    async (sessionId: string) => {
      const detail = await getSession(sessionId);
      persistActiveSession(sessionId);
      dispatch({ type: 'session/load', payload: detail });
    },
    [dispatch],
  );

  const createAndSelectSession = useCallback(async () => {
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

  const initializeApp = useCallback(async () => {
    try {
      const [healthResult, sessions] = await Promise.all([
        getHealth().catch(() => null),
        listSessions(),
      ]);

      dispatch({
        type: 'health/set',
        payload: healthResult ? healthResult.status : 'error',
      });
      dispatch({ type: 'sessions/set', payload: sessions });

      const targetSessionId = getPreferredSessionId(sessions);
      if (targetSessionId) {
        await loadSession(targetSessionId);
      } else {
        await createAndSelectSession();
      }

      dispatch({ type: 'bootstrap/complete' });
    } catch (error) {
      dispatch({
        type: 'bootstrap/error',
        payload: error instanceof Error ? error.message : '初始化失败',
      });
    }
  }, [createAndSelectSession, dispatch, loadSession]);

  const removeActiveSession = useCallback(async () => {
    if (!state.activeSessionId) {
      return;
    }

    await deleteSession(state.activeSessionId);
    const sessions = await refreshSessions();

    if (sessions.length === 0) {
      await createAndSelectSession();
      return;
    }

    const nextSessionId = getPreferredSessionId(sessions) ?? sessions[0].session_id;
    await loadSession(nextSessionId);
  }, [createAndSelectSession, loadSession, refreshSessions, state.activeSessionId]);

  return {
    initializeApp,
    refreshSessions,
    loadSession,
    createAndSelectSession,
    removeActiveSession,
  };
}
