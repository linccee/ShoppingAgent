import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ChatTimeline } from './ChatTimeline';

describe('ChatTimeline', () => {
  it('shows running and completed tool states', () => {
    render(
      <ChatTimeline
        isComplete={false}
        steps={[
          {
            type: 'tool',
            tool: 'search_products',
            input: { query: 'headphones' },
            output: '找到 3 个商品',
          },
          {
            type: 'tool',
            tool: 'prices',
            input: { sku: 'ABC' },
            output: '',
          },
        ]}
      />,
    );

    expect(screen.getByText('已完成')).toBeInTheDocument();
    expect(screen.getByText('处理中')).toBeInTheDocument();
  });
});
