import { useAuthStore } from '../../store/auth-store';
import { storage } from '../../utils/storage';

// Mock storage
jest.mock('../../utils/storage', () => ({
  storage: {
    setItem: jest.fn(),
    getItem: jest.fn(),
    deleteItem: jest.fn(),
  },
}));

describe('AuthStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    jest.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('should set token and update isAuthenticated', async () => {
    const token = 'test-token';
    await useAuthStore.getState().setToken(token);

    const state = useAuthStore.getState();
    expect(state.token).toBe(token);
    expect(state.isAuthenticated).toBe(true);
    expect(storage.setItem).toHaveBeenCalledWith('loom_session_token', token);
  });

  it('should set user and update isAuthenticated', () => {
    const user = { id: '1', username: 'test', github_user_id: 123 };
    useAuthStore.getState().setUser(user);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(user);
    expect(state.isAuthenticated).toBe(true);
  });

  it('should clear state on logout', async () => {
    useAuthStore.setState({
      user: { id: '1' } as any,
      token: 'some-token',
      isAuthenticated: true,
    });

    await useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(storage.deleteItem).toHaveBeenCalledWith('loom_session_token');
  });
});
