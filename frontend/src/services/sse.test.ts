import { afterEach, describe, expect, it, vi } from 'vitest';

import { createSseChunkParser, streamChat } from './sse';
import type { ChatEvent } from '../types';

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

afterEach(() => {
  vi.restoreAllMocks();
});

describe('createSseChunkParser', () => {
  it('parses split SSE frames into typed events', () => {
    const events: ChatEvent[] = [];
    const parser = createSseChunkParser((event) => events.push(event));

    parser.push('data: {"type":"session","data":{"session_id":"abc"},"session_id":""}\n\n');
    parser.push('data: {"type":"token","data":"你好","session_id":"abc"}\n');
    parser.push('\n');
    parser.flush();

    expect(events).toHaveLength(2);
    expect(events[0]).toMatchObject({
      type: 'session',
      data: { session_id: 'abc' },
    });
    expect(events[1]).toMatchObject({
      type: 'token',
      data: '你好',
      session_id: 'abc',
    });
  });

  it('passes AbortSignal to fetch when streaming chat', async () => {
    const localStorageMock = createLocalStorageMock();
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      configurable: true,
    });

    const controller = new AbortController();
    const fetchSpy = vi.fn().mockResolvedValue(
      new Response('', {
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
        },
      }),
    );

    vi.stubGlobal('fetch', fetchSpy);

    const request = {
      message: 'hello',
      session_id: 'session-1',
    };

    for await (const _event of streamChat(request, { signal: controller.signal })) {
      // No-op: this empty stream should end immediately.
    }

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/chat/stream'),
      expect.objectContaining({ signal: controller.signal }),
    );
  });
});
