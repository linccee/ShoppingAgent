import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { SessionList } from './SessionList';

describe('SessionList', () => {
  it('renders sessions and emits the selected id', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const onRequestDelete = vi.fn();

    render(
      <SessionList
        sessions={[
          {
            session_id: 'session-a',
            title: '耳机对比',
            updated_at: '2026-03-19T10:00:00Z',
            created_at: '2026-03-19T10:00:00Z',
          },
          {
            session_id: 'session-b',
            title: '显示器对比',
            updated_at: '2026-03-19T11:00:00Z',
            created_at: '2026-03-19T11:00:00Z',
          },
        ]}
        activeSessionId="session-a"
        onSelect={onSelect}
        onRequestDelete={onRequestDelete}
        isBusy={false}
      />,
    );

    await user.click(screen.getByRole('button', { name: /^显示器对比/ }));
    expect(onSelect).toHaveBeenCalledWith('session-b');
  });

  it('requests deletion without selecting the session', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const onRequestDelete = vi.fn();

    render(
      <SessionList
        sessions={[
          {
            session_id: 'session-a',
            title: '耳机对比',
            updated_at: '2026-03-19T10:00:00Z',
            created_at: '2026-03-19T10:00:00Z',
          },
        ]}
        activeSessionId="session-a"
        onSelect={onSelect}
        onRequestDelete={onRequestDelete}
        isBusy={false}
      />,
    );

    const sessionItem = screen.getByRole('button', { name: /^耳机对比/ }).closest('article');
    expect(sessionItem).not.toBeNull();

    await user.hover(sessionItem!);
    await user.click(screen.getByRole('button', { name: '删除会话 耳机对比' }));

    expect(onRequestDelete).toHaveBeenCalledWith(
      expect.objectContaining({ session_id: 'session-a' }),
    );
    expect(onSelect).not.toHaveBeenCalled();
  });
});
