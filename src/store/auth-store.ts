import { create } from 'zustand';
import { storage } from '@/utils/storage';
import { User, AuthState } from '@/types/auth';

const TOKEN_KEY = 'loom_session_token';

interface AuthActions {
  token: string | null;
  setToken: (token: string) => Promise<void>;
  getToken: () => Promise<string | null>;
  setUser: (user: User | null) => void;
  setError: (error: string | null) => void;
  setLoading: (isLoading: boolean) => void;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState & AuthActions>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true, // Start in loading state until session is checked
  error: null,

  setToken: async (token: string) => {
    await storage.setItem(TOKEN_KEY, token);
    set({ isAuthenticated: true, token });
  },

  getToken: async () => {
    return await storage.getItem(TOKEN_KEY);
  },

  setUser: (user: User | null) => {
    set({ user, isAuthenticated: !!user });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setLoading: (isLoading: boolean) => {
    set({ isLoading });
  },

  logout: async () => {
    await storage.deleteItem(TOKEN_KEY);
    set({ user: null, token: null, isAuthenticated: false, error: null });
  },
}));
