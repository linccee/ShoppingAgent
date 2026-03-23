import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      username: 'demo-user',
      email: 'demo@example.com',
    },
    logout: vi.fn(),
  }),
}));

import { Sidebar } from './Sidebar';

describe('Sidebar', () => {
  it('renders a clear logout action in the user card', () => {
    render(
      <MemoryRouter>
        <Sidebar
          sessions={[]}
          activeSessionId={null}
          messages={[]}
          inputTokens={0}
          outputTokens={0}
          health="ok"
          runtimeConfig={{
            model: 'gpt-test',
            temperature: 0,
            max_tokens: 4000,
            memory_turns: 10,
          }}
          isBusy={false}
          onSelectSession={vi.fn()}
          onNewSession={vi.fn()}
          onDeleteCurrent={vi.fn()}
          onDeleteSession={vi.fn()}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole('button', { name: '退出登录' })).toHaveTextContent('登出');
  });

  it('confirms session deletion before invoking the removal callback', async () => {
    const user = userEvent.setup();
    const onDeleteSession = vi.fn().mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <Sidebar
          sessions={[
            {
              session_id: 'session-a',
              title: '耳机对比',
              updated_at: '2026-03-19T10:00:00Z',
              created_at: '2026-03-19T10:00:00Z',
            },
          ]}
          activeSessionId="session-a"
          messages={[]}
          inputTokens={0}
          outputTokens={0}
          health="ok"
          runtimeConfig={{
            model: 'gpt-test',
            temperature: 0,
            max_tokens: 4000,
            memory_turns: 10,
          }}
          isBusy={false}
          onSelectSession={vi.fn()}
          onNewSession={vi.fn()}
          onDeleteCurrent={vi.fn()}
          onDeleteSession={onDeleteSession}
        />
      </MemoryRouter>,
    );

    const sessionItem = screen.getByRole('button', { name: /^耳机对比/ }).closest('article');
    expect(sessionItem).not.toBeNull();

    await user.hover(sessionItem!);
    await user.click(screen.getByRole('button', { name: '删除会话 耳机对比' }));

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '确认删除' }));

    expect(onDeleteSession).toHaveBeenCalledWith('session-a');
  });
});
