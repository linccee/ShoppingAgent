import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ChatInput } from './ChatInput';

describe('ChatInput', () => {
  it('submits content and resets the textarea', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <ChatInput
        isStreaming={false}
        isStopping={false}
        onSubmit={onSubmit}
        onStop={vi.fn()}
      />,
    );

    await user.type(
      screen.getByPlaceholderText('描述你的购买目标，例如：帮我挑一台预算 ¥3000 左右的降噪耳机'),
      '帮我比较一下 iPad 和 Surface',
    );
    await user.click(screen.getByRole('button', { name: '发送' }));

    expect(onSubmit).toHaveBeenCalledWith('帮我比较一下 iPad 和 Surface');
    expect(screen.getByRole('textbox')).toHaveValue('');
  });

  it('switches into stop mode while streaming', () => {
    render(
      <ChatInput
        isStreaming
        isStopping={false}
        onSubmit={vi.fn()}
        onStop={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: '停止生成' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '发送' })).not.toBeInTheDocument();
  });
});
