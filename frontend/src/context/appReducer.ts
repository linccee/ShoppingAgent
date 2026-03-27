import type { AppState, Message, SessionDetail, SessionSummary, TokenUsage, ToolStep } from '../types';

export const initialAppState: AppState = {
  sessions: [],
  activeSessionId: null,
  messages: [],
  inputTokens: 0,
  outputTokens: 0,
  health: 'loading',
  runtimeConfig: {
    model: null,
    temperature: 0,
    max_tokens: 0,
    memory_turns: 0,
  },
  isStreaming: false,
  isStopping: false,
  isBootstrapping: true,
  error: null,
};

export type AppAction =
  | { type: 'bootstrap/complete' }
  | { type: 'bootstrap/error'; payload: string }
  | {
      type: 'health/set';
      payload: {
        health: AppState['health'];
        runtimeConfig: AppState['runtimeConfig'];
      };
    }
  | { type: 'sessions/set'; payload: SessionSummary[] }
  | { type: 'session/load'; payload: SessionDetail }
  | { type: 'session/create'; payload: SessionDetail }
  | { type: 'stream/start'; payload: { content: string } }
  | { type: 'stream/session'; payload: { sessionId: string } }
  | { type: 'stream/token'; payload: string }
  | { type: 'stream/toolStart'; payload: ToolStep }
  | { type: 'stream/toolEnd'; payload: string }
  | { type: 'stream/tokenUsage'; payload: TokenUsage }
  | { type: 'stream/stopping' }
  | { type: 'stream/stopped' }
  | { type: 'stream/error'; payload: string }
  | { type: 'stream/finish' }
  | { type: 'error/clear' };

export function deriveSessionTitle(content: string): string {
  const trimmed = content.trim();
  if (!trimmed) {
    return '新的对话';
  }
  return trimmed.length > 20 ? `${trimmed.slice(0, 20)}...` : trimmed;
}

function updateAssistantMessage(messages: Message[], updater: (message: Message) => Message): Message[] {
  const nextMessages = [...messages];

  for (let index = nextMessages.length - 1; index >= 0; index -= 1) {
    if (nextMessages[index]?.role === 'assistant') {
      nextMessages[index] = updater(nextMessages[index]);
      return nextMessages;
    }
  }

  return nextMessages;
}

function upsertSession(
  sessions: SessionSummary[],
  sessionId: string,
  title: string,
): SessionSummary[] {
  const existing = sessions.find((session) => session.session_id === sessionId);
  const summary: SessionSummary = {
    session_id: sessionId,
    title,
    updated_at: new Date().toISOString(),
    created_at: existing?.created_at ?? new Date().toISOString(),
  };

  return [summary, ...sessions.filter((session) => session.session_id !== sessionId)];
}

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'bootstrap/complete':
      return {
        ...state,
        isBootstrapping: false,
        error: null,
      };
    case 'bootstrap/error':
      return {
        ...state,
        isBootstrapping: false,
        error: action.payload,
      };
    case 'health/set':
      return {
        ...state,
        health: action.payload.health,
        runtimeConfig: action.payload.runtimeConfig,
      };
    case 'sessions/set':
      return {
        ...state,
        sessions: action.payload,
      };
    case 'session/load':
    case 'session/create':
      return {
        ...state,
        activeSessionId: action.payload.session_id,
        messages: action.payload.messages,
        inputTokens: action.payload.input_tokens,
        outputTokens: action.payload.output_tokens,
        isStreaming: false,
        isStopping: false,
        error: null,
      };
    case 'stream/start': {
      const sessionId = state.activeSessionId;
      const nextMessages: Message[] = [
        ...state.messages,
        { role: 'user', content: action.payload.content },
        { role: 'assistant', content: '', steps: [] },
      ];

      return {
        ...state,
        messages: nextMessages,
        sessions: sessionId ? upsertSession(state.sessions, sessionId, deriveSessionTitle(action.payload.content)) : state.sessions,
        isStreaming: true,
        isStopping: false,
        error: null,
      };
    }
    case 'stream/session':
      return {
        ...state,
        activeSessionId: action.payload.sessionId,
        sessions: upsertSession(
          state.sessions,
          action.payload.sessionId,
          deriveSessionTitle(
            [...state.messages]
              .reverse()
              .find((message) => message.role === 'user')
              ?.content ?? '新的对话',
          ),
        ),
      };
    case 'stream/token':
      return {
        ...state,
        messages: updateAssistantMessage(state.messages, (message) => ({
          ...message,
          content: `${message.content}${action.payload}`,
        })),
      };
    case 'stream/toolStart':
      return {
        ...state,
        messages: updateAssistantMessage(state.messages, (message) => ({
          ...message,
          steps: [...(message.steps ?? []), action.payload],
        })),
      };
    case 'stream/toolEnd':
      return {
        ...state,
        messages: updateAssistantMessage(state.messages, (message) => {
          const steps = [...(message.steps ?? [])];
          if (steps.length > 0) {
            const lastIndex = steps.length - 1;
            steps[lastIndex] = {
              ...steps[lastIndex],
              output: action.payload,
            };
          }
          return {
            ...message,
            steps,
          };
        }),
      };
    case 'stream/tokenUsage':
      return {
        ...state,
        inputTokens: state.inputTokens + (action.payload.input_tokens ?? 0),
        outputTokens: state.outputTokens + (action.payload.output_tokens ?? 0),
      };
    case 'stream/stopping':
      return {
        ...state,
        isStopping: true,
      };
    case 'stream/stopped':
      return {
        ...state,
        isStopping: false,
      };
    case 'stream/error':
      return {
        ...state,
        error: action.payload,
        messages: updateAssistantMessage(state.messages, (message) => ({
          ...message,
          content: message.content
            ? `${message.content}\n\n⚠️ ${action.payload}`
            : `⚠️ ${action.payload}`,
        })),
      };
    case 'stream/finish':
      return {
        ...state,
        isStreaming: false,
        isStopping: false,
      };
    case 'error/clear':
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
}
