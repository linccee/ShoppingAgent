import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

  it('shows an explicit expand and collapse control', async () => {
    const user = userEvent.setup();
    render(
      <ChatTimeline
        isComplete
        steps={[
          {
            type: 'tool',
            tool: 'search_products',
            input: { query: 'headphones' },
            output: '找到 3 个商品',
          },
        ]}
      />,
    );

    expect(screen.getByText('展开')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /轨迹回放/ })).toHaveAttribute('aria-expanded', 'false');

    await user.click(screen.getByRole('button', { name: /轨迹回放/ }));

    expect(screen.getByText('收起')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /轨迹回放/ })).toHaveAttribute('aria-expanded', 'true');
  });
});
