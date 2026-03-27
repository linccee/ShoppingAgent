import { describe, expect, it } from 'vitest';

import { appReducer, initialAppState } from './appReducer';

describe('appReducer', () => {
  it('restores persisted session stats when a session is loaded', () => {
    const loaded = appReducer(initialAppState, {
      type: 'session/load',
      payload: {
        session_id: 'session-a',
        title: '耳机对比',
        updated_at: '2026-03-23T12:00:00Z',
        created_at: '2026-03-23T11:00:00Z',
        messages: [
          { role: 'user', content: '帮我比较两款耳机' },
          {
            role: 'assistant',
            content: '已整理核心差异',
            steps: [
              {
                type: 'tool',
                tool: 'search_products',
                input: { query: 'headphones' },
                output: '找到 2 个结果',
              },
            ],
          },
        ],
        input_tokens: 321,
        output_tokens: 123,
      },
    });

    expect(loaded.activeSessionId).toBe('session-a');
    expect(loaded.messages).toHaveLength(2);
    expect(loaded.inputTokens).toBe(321);
    expect(loaded.outputTokens).toBe(123);
  });

  it('accumulates streaming events into the assistant message', () => {
    const started = appReducer(initialAppState, {
      type: 'stream/start',
      payload: { content: '推荐一个 27 寸显示器' },
    });

    const withTool = appReducer(started, {
      type: 'stream/toolStart',
      payload: {
        type: 'tool',
        tool: 'search_products',
        input: { query: 'monitor' },
        output: '',
      },
    });

    const withToolResult = appReducer(withTool, {
      type: 'stream/toolEnd',
      payload: '找到 3 个候选商品',
    });

    const withToken = appReducer(withToolResult, {
      type: 'stream/token',
      payload: '这三款里我更推荐第二款。',
    });

    const withUsage = appReducer(withToken, {
      type: 'stream/tokenUsage',
      payload: {
        input_tokens: 120,
        output_tokens: 45,
      },
    });

    const finished = appReducer(withUsage, { type: 'stream/finish' });

    expect(finished.isStreaming).toBe(false);
    expect(finished.messages[finished.messages.length - 1]?.content).toContain('第二款');
    expect(finished.messages[finished.messages.length - 1]?.steps?.[0].output).toBe('找到 3 个候选商品');
    expect(finished.inputTokens).toBe(120);
    expect(finished.outputTokens).toBe(45);
  });
});
