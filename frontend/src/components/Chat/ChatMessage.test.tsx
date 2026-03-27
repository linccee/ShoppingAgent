import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ChatMessage } from './ChatMessage';

describe('ChatMessage', () => {
  it('renders assistant replies as markdown', () => {
    render(
      <ChatMessage
        isStreamingMessage={false}
        message={{
          role: 'assistant',
          content: '## 购物推荐\n\n- **首选**：[iPhone 15 Pro](https://example.com)',
          steps: [],
        }}
      />,
    );

    expect(screen.getByRole('heading', { level: 2, name: '购物推荐' })).toBeInTheDocument();
    expect(screen.getByText('首选')).toContainHTML('strong');
    expect(screen.getByRole('link', { name: 'iPhone 15 Pro' })).toHaveAttribute(
      'href',
      'https://example.com',
    );
  });

  it('keeps user messages as plain text', () => {
    render(
      <ChatMessage
        isStreamingMessage={false}
        message={{
          role: 'user',
          content: '**不要**解析成 markdown',
        }}
      />,
    );

    expect(screen.getByText('**不要**解析成 markdown')).toBeInTheDocument();
  });
});
