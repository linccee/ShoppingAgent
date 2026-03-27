import { describe, expect, it } from 'vitest';

import { createSseChunkParser } from './sse';
import type { ChatEvent } from '../types';

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
});
