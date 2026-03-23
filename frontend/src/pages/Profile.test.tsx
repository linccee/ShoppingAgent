import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  navigateMock,
  logoutMock,
  getCurrentUserMock,
  updatePreferencesMock,
} = vi.hoisted(() => ({
  navigateMock: vi.fn(),
  logoutMock: vi.fn(),
  getCurrentUserMock: vi.fn(),
  updatePreferencesMock: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      username: 'demo-user',
      email: 'demo@example.com',
    },
    logout: logoutMock,
  }),
}));

vi.mock('../api/user', () => ({
  userApi: {
    getCurrentUser: getCurrentUserMock,
    updatePreferences: updatePreferencesMock,
  },
}));

import Profile from './Profile';

describe('Profile', () => {
  beforeEach(() => {
    navigateMock.mockReset();
    logoutMock.mockReset();
    updatePreferencesMock.mockReset();
    getCurrentUserMock.mockReset();
    getCurrentUserMock.mockResolvedValue({
      data: {
        preferences: {
          default_currency: 'CNY',
          favorite_platforms: [],
          budget_range: { min: 0, max: 0 },
          notification_enabled: false,
        },
      },
    });
  });

  it('shows a back button that returns to chat', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Profile />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: '个人设置' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '返回聊天' }));

    expect(navigateMock).toHaveBeenCalledWith('/chat');
  });
});
