import { useCallback } from 'react';

import { useAppDispatch, useAppState } from '../context/useAppStore';
import { listSessions, stopChat } from '../services/api';
import { streamChat } from '../services/sse';
import { logger } from '../utils/logger';

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

      logger.info('Chat', `Sending message: ${trimmed.substring(0, 50)}...`);
      dispatch({ type: 'stream/start', payload: { content: trimmed } });

      try {
        for await (const event of streamChat({
          message: trimmed,
          session_id: state.activeSessionId,
        })) {
          switch (event.type) {
            case 'session':
              logger.debug('Chat', `Session established: ${event.data.session_id}`);
              window.localStorage.setItem(ACTIVE_SESSION_KEY, event.data.session_id);
              dispatch({ type: 'stream/session', payload: { sessionId: event.data.session_id } });
              break;
            case 'token':
              dispatch({ type: 'stream/token', payload: event.data });
              break;
            case 'tool_start':
              logger.debug('Chat', `Tool started: ${event.data.tool}`);
              dispatch({ type: 'stream/toolStart', payload: event.data });
              break;
            case 'tool_end':
              logger.debug('Chat', 'Tool ended');
              dispatch({ type: 'stream/toolEnd', payload: event.data });
              break;
            case 'token_usage':
              logger.debug('Chat', `Token usage: input=${event.data.input_tokens}, output=${event.data.output_tokens}`);
              dispatch({ type: 'stream/tokenUsage', payload: event.data });
              break;
            case 'stopped':
              logger.info('Chat', 'Stream stopped');
              dispatch({ type: 'stream/stopped' });
              break;
            case 'error':
              logger.error('Chat', `Stream error: ${event.data}`);
              dispatch({ type: 'stream/error', payload: event.data });
              break;
            case 'done':
              logger.info('Chat', 'Stream completed');
              break;
            default:
              break;
          }
        }
      } catch (error) {
        logger.error('Chat', 'Send message failed', error instanceof Error ? error.message : 'Unknown error');
        dispatch({
          type: 'stream/error',
          payload: error instanceof Error ? error.message : '消息发送失败',
        });
      } finally {
        try {
          const sessions = await listSessions();
          dispatch({ type: 'sessions/set', payload: sessions });
        } catch (e) {
          logger.warn('Chat', 'Failed to refresh sessions', e instanceof Error ? e.message : 'Unknown error');
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

    logger.info('Chat', `Stopping generation for session ${state.activeSessionId}`);
    dispatch({ type: 'stream/stopping' });

    try {
      const response = await stopChat(state.activeSessionId);
      if (!response.accepted) {
        logger.warn('Chat', 'Stop request not accepted');
        dispatch({ type: 'stream/error', payload: '当前没有可停止的生成任务' });
        dispatch({ type: 'stream/finish' });
      }
    } catch (error) {
      logger.error('Chat', 'Stop generation failed', error instanceof Error ? error.message : 'Unknown error');
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
