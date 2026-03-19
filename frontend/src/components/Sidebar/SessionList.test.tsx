import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { SessionList } from './SessionList';

describe('SessionList', () => {
  it('renders sessions and emits the selected id', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

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
      />,
    );

    await user.click(screen.getByRole('button', { name: /显示器对比/ }));
    expect(onSelect).toHaveBeenCalledWith('session-b');
  });
});
