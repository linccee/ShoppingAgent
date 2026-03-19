import type {
  HealthResponse,
  SessionCreateResponse,
  SessionDetail,
  SessionSummary,
  StopChatResponse,
} from '../types';

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export function getApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
  return configured.replace(/\/$/, '');
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`.trim();
    try {
      const body = (await response.json()) as { detail?: string; message?: string };
      detail = body.detail ?? body.message ?? detail;
    } catch {
      // Ignore non-JSON error payloads.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export function listSessions(): Promise<SessionSummary[]> {
  return request<SessionSummary[]>('/sessions');
}

export function createSession(): Promise<SessionCreateResponse> {
  return request<SessionCreateResponse>('/sessions', { method: 'POST' });
}

export function getSession(sessionId: string): Promise<SessionDetail> {
  return request<SessionDetail>(`/sessions/${sessionId}`);
}

export function deleteSession(sessionId: string): Promise<void> {
  return request<void>(`/sessions/${sessionId}`, { method: 'DELETE' });
}

export function stopChat(sessionId: string): Promise<StopChatResponse> {
  return request<StopChatResponse>('/chat/stop', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}
