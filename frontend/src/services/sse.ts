import type { ChatEvent, ChatStreamRequest, RawChatEvent, ToolStep } from '../types';
import { getApiBaseUrl } from './api';

function parseFrame(frame: string, onEvent: (event: ChatEvent) => void): void {
  const dataLines = frame
    .split('\n')
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trimStart());

  if (dataLines.length === 0) {
    return;
  }

  const payload = JSON.parse(dataLines.join('\n')) as RawChatEvent;
  onEvent(normalizeChatEvent(payload));
}

export function createSseChunkParser(onEvent: (event: ChatEvent) => void) {
  let buffer = '';

  return {
    push(chunk: string) {
      buffer += chunk;
      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';
      for (const frame of frames) {
        if (frame.trim()) {
          parseFrame(frame, onEvent);
        }
      }
    },
    flush() {
      if (buffer.trim()) {
        parseFrame(buffer, onEvent);
      }
      buffer = '';
    },
  };
}

function normalizeChatEvent(payload: RawChatEvent): ChatEvent {
  switch (payload.type) {
    case 'session':
      return {
        type: 'session',
        data: payload.data as { session_id: string },
        session_id: payload.session_id,
      };
    case 'token':
      return { type: 'token', data: String(payload.data ?? ''), session_id: payload.session_id };
    case 'tool_start':
      return {
        type: 'tool_start',
        data: payload.data as ToolStep,
        session_id: payload.session_id,
      };
    case 'tool_end':
      return { type: 'tool_end', data: String(payload.data ?? ''), session_id: payload.session_id };
    case 'token_usage':
      return {
        type: 'token_usage',
        data: (payload.data ?? {}) as { input_tokens?: number; output_tokens?: number },
        session_id: payload.session_id,
      };
    case 'error':
      return { type: 'error', data: String(payload.data ?? ''), session_id: payload.session_id };
    case 'stopped':
      return { type: 'stopped', data: String(payload.data ?? ''), session_id: payload.session_id };
    case 'done':
      return {
        type: 'done',
        data: (payload.data ?? { message: 'completed' }) as { message: string },
        session_id: payload.session_id,
      };
    default:
      throw new Error(`Unsupported SSE event type: ${payload.type}`);
  }
}

export async function* streamChat(request: ChatStreamRequest): AsyncGenerator<ChatEvent> {
  const response = await fetch(`${getApiBaseUrl()}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Unable to stream chat: ${response.status}`);
  }

  if (!response.body) {
    throw new Error('Streaming response body is unavailable');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const pendingEvents: ChatEvent[] = [];
  const parser = createSseChunkParser((event) => pendingEvents.push(event));

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      parser.push(decoder.decode());
      parser.flush();
      while (pendingEvents.length > 0) {
        yield pendingEvents.shift()!;
      }
      break;
    }

    parser.push(decoder.decode(value, { stream: true }));
    while (pendingEvents.length > 0) {
      yield pendingEvents.shift()!;
    }
  }
}
