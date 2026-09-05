import * as WebBrowser from 'expo-web-browser';
import * as AuthSession from 'expo-auth-session';
import apiClient from './api-client';
import { AuthorizeResponse, AuthResponse, User } from '@/types/auth';
import { useAuthStore } from '@/store/auth-store';

WebBrowser.maybeCompleteAuthSession();

export class AuthService {
  static async startGitHubLogin() {
    const store = useAuthStore.getState();
    store.setLoading(true);
    store.setError(null);

    try {
      // 1. Get authorization URL from backend
      const { data: authorizeData } = await apiClient.get<AuthorizeResponse>('/api/v1/auth/github/authorize');

      // 2. Open browser for GitHub OAuth flow
      const result = await WebBrowser.openAuthSessionAsync(
        authorizeData.authorization_url,
        AuthSession.makeRedirectUri()
      );

      if (result.type === 'success') {
        const { url } = result;
        const params = new URL(url).searchParams;
        const code = params.get('code');
        const state = params.get('state');

        if (code && state) {
          // 3. Exchange code for Loom session token via backend
          const { data: authData } = await apiClient.get<AuthResponse>('/api/v1/auth/github/callback', {
            params: { code, state }
          });

          await store.setToken(authData.access_token);
          store.setUser(authData.user);
        } else {
          throw new Error('Authentication cancelled or failed');
        }
      } else {
        store.setLoading(false);
      }
    } catch (error: any) {
      store.setError(error.message || 'Failed to sign in with GitHub');
      store.setLoading(false);
    }
  }

  static async fetchCurrentUser() {
    const store = useAuthStore.getState();
    const token = await store.getToken();

    if (!token) {
      store.setLoading(false);
      return;
    }

    try {
      const { data: user } = await apiClient.get<User>('/api/v1/me');
      store.setUser(user);
    } catch (error) {
      // Token probably expired
      await store.logout();
    } finally {
      store.setLoading(false);
    }
  }

  static async logout() {
    const store = useAuthStore.getState();
    try {
      await apiClient.post('/api/v1/auth/logout');
    } catch (error) {
      // Ignore logout errors
    } finally {
      await store.logout();
    }
  }
}
