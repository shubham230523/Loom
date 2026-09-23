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

      // Check for standalone mock mode
      if (authorizeData.authorization_url === '#') {
        const demoUser = {
          id: 1,
          github_id: 12345,
          username: 'loom-demo-user',
          avatar_url: 'https://github.com/ghost.png',
        };
        await store.setToken('demo-access-token');
        store.setUser(demoUser);
        store.setLoading(false);
        return;
      }

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
          store.setLoading(false);
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

    // Check if we are inside an OAuth callback popup window on Web
    if (typeof window !== 'undefined' && window.location.search) {
      const search = window.location.search;
      if (search.includes('code=') || search.includes('state=')) {
        // Do NOT auto-login or redirect in the popup window.
        // Let WebBrowser.maybeCompleteAuthSession() pass the code to the parent window and close this popup.
        store.setLoading(false);
        return;
      }
    }

    let token = await store.getToken();

    if (!token) {
      // In web standalone demo mode, default to demo session
      token = 'demo-access-token';
      await store.setToken(token);
    }

    try {
      const { data: user } = await apiClient.get<User>('/api/v1/auth/me');
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
