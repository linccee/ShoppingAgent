export type HealthState = 'loading' | 'ok' | 'degraded' | 'error';

export interface ToolStep {
  type: 'tool';
  tool: string;
  input: unknown;
  output: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  steps?: ToolStep[];
}

export interface SessionSummary {
  session_id: string;
  title: string;
  updated_at: string | null;
  created_at: string | null;
}

export interface SessionDetail extends SessionSummary {
  messages: Message[];
  input_tokens: number;
  output_tokens: number;
}

export interface SessionCreateResponse {
  session_id: string;
}

export interface StopChatResponse {
  accepted: boolean;
  session_id: string;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  mongo: 'up' | 'down';
}

export interface TokenUsage {
  input_tokens?: number;
  output_tokens?: number;
}

export interface ChatStreamRequest {
  message: string;
  session_id: string | null;
}

export interface SessionEvent {
  type: 'session';
  data: { session_id: string };
  session_id: string;
}

export interface TokenEvent {
  type: 'token';
  data: string;
  session_id: string;
}

export interface ToolStartEvent {
  type: 'tool_start';
  data: ToolStep;
  session_id: string;
}

export interface ToolEndEvent {
  type: 'tool_end';
  data: string;
  session_id: string;
}

export interface TokenUsageEvent {
  type: 'token_usage';
  data: TokenUsage;
  session_id: string;
}

export interface ErrorEvent {
  type: 'error';
  data: string;
  session_id: string;
}

export interface StoppedEvent {
  type: 'stopped';
  data: string;
  session_id: string;
}

export interface DoneEvent {
  type: 'done';
  data: { message: string };
  session_id: string;
}

export type ChatEvent =
  | SessionEvent
  | TokenEvent
  | ToolStartEvent
  | ToolEndEvent
  | TokenUsageEvent
  | ErrorEvent
  | StoppedEvent
  | DoneEvent;

export interface RawChatEvent {
  type: string;
  data: unknown;
  session_id: string;
}

export interface AppState {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  messages: Message[];
  inputTokens: number;
  outputTokens: number;
  health: HealthState;
  isStreaming: boolean;
  isStopping: boolean;
  isBootstrapping: boolean;
  error: string | null;
}
