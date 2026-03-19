import { describe, expect, it } from 'vitest';

import { appReducer, initialAppState } from './appReducer';

describe('appReducer', () => {
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
