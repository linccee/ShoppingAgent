import { useCallback } from 'react';

import { useAppDispatch, useAppState } from '../context/useAppStore';
import { listSessions, stopChat } from '../services/api';
import { streamChat } from '../services/sse';

const ACTIVE_SESSION_KEY = 'mirror-curation.active-session-id';

export function useChat() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || state.isStreaming || !state.activeSessionId) {
        return;
      }

      dispatch({ type: 'stream/start', payload: { content: trimmed } });

      try {
        for await (const event of streamChat({
          message: trimmed,
          session_id: state.activeSessionId,
        })) {
          switch (event.type) {
            case 'session':
              window.localStorage.setItem(ACTIVE_SESSION_KEY, event.data.session_id);
              dispatch({ type: 'stream/session', payload: { sessionId: event.data.session_id } });
              break;
            case 'token':
              dispatch({ type: 'stream/token', payload: event.data });
              break;
            case 'tool_start':
              dispatch({ type: 'stream/toolStart', payload: event.data });
              break;
            case 'tool_end':
              dispatch({ type: 'stream/toolEnd', payload: event.data });
              break;
            case 'token_usage':
              dispatch({ type: 'stream/tokenUsage', payload: event.data });
              break;
            case 'stopped':
              dispatch({ type: 'stream/stopped' });
              break;
            case 'error':
              dispatch({ type: 'stream/error', payload: event.data });
              break;
            case 'done':
              break;
            default:
              break;
          }
        }
      } catch (error) {
        dispatch({
          type: 'stream/error',
          payload: error instanceof Error ? error.message : '消息发送失败',
        });
      } finally {
        try {
          const sessions = await listSessions();
          dispatch({ type: 'sessions/set', payload: sessions });
        } catch {
          // Best-effort refresh to keep the sidebar up to date.
        }
        dispatch({ type: 'stream/finish' });
      }
    },
    [dispatch, state.activeSessionId, state.isStreaming],
  );

  const stopGeneration = useCallback(async () => {
    if (!state.activeSessionId || !state.isStreaming || state.isStopping) {
      return;
    }

    dispatch({ type: 'stream/stopping' });

    try {
      const response = await stopChat(state.activeSessionId);
      if (!response.accepted) {
        dispatch({ type: 'stream/error', payload: '当前没有可停止的生成任务' });
        dispatch({ type: 'stream/finish' });
      }
    } catch (error) {
      dispatch({
        type: 'stream/error',
        payload: error instanceof Error ? error.message : '停止生成失败',
      });
      dispatch({ type: 'stream/finish' });
    }
  }, [dispatch, state.activeSessionId, state.isStopping, state.isStreaming]);

  return {
    sendMessage,
    stopGeneration,
  };
}
