import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { ApiError, ApiErrorResponse } from '@/types/api';
import { useAuthStore } from '@/store/auth-store';

const DEFAULT_TIMEOUT = 300000; // 5 minutes (increased for long running autonomous AI operations)

// For local development with Android Emulator, use 10.0.2.2 instead of localhost
const getBaseUrl = () => {
  return process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
};

const apiClient: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await useAuthStore.getState().getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Fallback Mock Generator for Static Web Demos (GitHub Pages) when Backend is Offline
const getMockResponse = (url: string = '') => {
  console.log(`[Standalone Web Demo] Intercepted request to ${url} - Returning fallback mock data.`);

  if (url.includes('/health')) {
    return { data: { status: 'ok', mode: 'demo_mock' } };
  }

  if (url.includes('/auth/me')) {
    return {
      data: {
        id: 1,
        github_id: 12345,
        username: 'loom-demo-user',
        email: 'demo@loom.dev',
        avatar_url: 'https://github.com/ghost.png',
      },
    };
  }

  if (url.includes('/auth/github/authorize')) {
    return { data: { authorization_url: '#' } };
  }

  if (url.includes('/auth/github/callback')) {
    return {
      data: {
        access_token: 'demo-access-token',
        user: {
          id: 1,
          github_id: 12345,
          username: 'loom-demo-user',
          avatar_url: 'https://github.com/ghost.png',
        },
      },
    };
  }

  if (url.includes('/auth/logout')) {
    return { data: { status: 'success' } };
  }

  if (url.includes('/repositories/search')) {
    return {
      data: {
        items: [
          {
            id: 101,
            full_name: 'facebook/react',
            name: 'react',
            description: 'The library for web and native user interfaces.',
            stars: 220000,
            language: 'JavaScript',
            owner: { login: 'facebook', avatar_url: 'https://github.com/facebook.png' },
            loom_id: 'dummy-repo-react',
            is_imported: true,
          },
          {
            id: 102,
            full_name: 'facebook/react-native',
            name: 'react-native',
            description: 'A framework for building native applications using React.',
            stars: 115000,
            language: 'TypeScript',
            owner: { login: 'facebook', avatar_url: 'https://github.com/facebook.png' },
            loom_id: 'dummy-repo-rn',
            is_imported: true,
          },
          {
            id: 103,
            full_name: 'expo/expo',
            name: 'expo',
            description: 'An open-source platform for making universal native apps for Android, iOS, and the web.',
            stars: 35000,
            language: 'TypeScript',
            owner: { login: 'expo', avatar_url: 'https://github.com/expo.png' },
            loom_id: 'dummy-repo-expo',
            is_imported: true,
          },
          {
            id: 104,
            full_name: 'shubham230523/Loom',
            name: 'Loom',
            description: 'AI-Powered Open-Source Contribution Platform',
            stars: 42,
            language: 'TypeScript',
            owner: { login: 'shubham230523', avatar_url: 'https://github.com/ghost.png' },
            loom_id: 'dummy-repo-loom',
            is_imported: true,
          },
        ],
        total: 4,
      },
    };
  }

  if (url.includes('/initialize')) {
    return {
      data: {
        id: 'dummy-repo-123',
        github_id: 104,
        full_name: 'shubham230523/Loom',
        name: 'Loom',
        stars: 42,
        language: 'TypeScript',
      },
    };
  }

  if (url.includes('/opportunities/discover')) {
    return { data: { status: 'synced', count: 2 } };
  }

  if (url.includes('/opportunities')) {
    return {
      data: [
        {
          id: 'dummy-opp-123',
          title: 'Fix overlapping token refresh requests in Auth Loop',
          category: 'bug_fix',
          difficulty: 'Medium',
          impact: 'High',
          confidence: 0.95,
          description: 'Concurrent API calls fail when token expires because multiple refresh calls trigger simultaneously.',
          suggested_approach: 'Deduplicate refresh requests by caching the pending promise in AuthClient.',
          repository_id: 'dummy-repo-123',
        },
        {
          id: 'dummy-opp-456',
          title: 'Add test suite for Agent State Transitions',
          category: 'test_coverage',
          difficulty: 'Easy',
          impact: 'Medium',
          confidence: 0.88,
          description: 'Improve unit test coverage for solution planner state changes.',
          suggested_approach: 'Add Jest test suite covering all state transitions in agent-ws.service.ts',
          repository_id: 'dummy-repo-123',
        },
      ],
    };
  }

  if (url.includes('/recommendations')) {
    return {
      data: [
        {
          opportunity: {
            id: 'dummy-opp-123',
            title: 'Fix overlapping token refresh requests in Auth Loop',
            category: 'bug_fix',
            difficulty: 'Medium',
            impact: 'High',
            confidence: 0.95,
            description: 'Concurrent API calls fail when token expires because multiple refresh calls trigger simultaneously.',
            suggested_approach: 'Deduplicate refresh requests by caching the pending promise in AuthClient.',
          },
          repository: {
            id: 'dummy-repo-123',
            full_name: 'shubham230523/Loom',
            language: 'TypeScript',
          },
        },
      ],
    };
  }

  if (url.includes('/plan')) {
    return {
      data: {
        agent_run_id: 'dummy-run-456',
        result: {
          id: 'dummy-plan-789',
          problem: 'The current user authentication loop fails to handle overlapping token refresh requests, leading to multiple simultaneous refresh calls.',
          target_files: ['src/services/api-client.ts', 'src/services/auth.service.ts'],
          relevant_symbols: ['refreshSession', 'apiClient.interceptors'],
          testing_strategy: 'Simulate 5 concurrent API calls with an expired token and verify only 1 refresh network call occurs.',
          steps: [
            '1. Intercept 401 Unauthorized responses in apiClient',
            '2. Hold concurrent requests in a queue while refreshing',
            '3. Retry failed queued requests once new token is obtained',
            '4. Add unit tests for token refresh deduplication',
          ],
        },
      },
    };
  }

  if (url.includes('/approve')) {
    return { data: { id: 'dummy-plan-789', approved: true } };
  }

  if (url.includes('/workspace')) {
    return { data: { workspace_id: 'demo-workspace-123', path: '/loom-workspaces/demo' } };
  }

  if (url.includes('/implement') || url.includes('/mock-implement')) {
    return {
      data: {
        status: 'success',
        pr_url: 'https://github.com/shubham230523/Loom/pull/42',
        branch: 'ai/dummy-refactor-auth-loop',
        agent_run_id: 'dummy-run-456',
      },
    };
  }

  if (url.includes('/validate')) {
    return {
      data: {
        is_valid: true,
        score: 100,
        summary: 'Mock Mode: Automatic 100% readiness for demonstration.',
        issues: [],
      },
    };
  }

  if (url.includes('/push')) {
    return {
      data: {
        status: 'pushed',
        branch: 'ai/dummy-refactor-auth-loop',
        repository: 'shubham230523/Loom',
      },
    };
  }

  if (url.includes('/pull-request')) {
    return {
      data: {
        id: 999,
        number: 42,
        url: 'https://github.com/shubham230523/Loom/pull/42',
        title: 'Fix token refresh in Auth Loop',
      },
    };
  }

  if (url.includes('/contributions')) {
    return {
      data: {
        id: 'dummy-contrib-123',
        repository_id: 'dummy-repo-123',
        opportunity_id: 'dummy-opp-123',
        status: 'completed',
        agent_run_id: 'dummy-run-456',
      },
    };
  }

  if (url.includes('/repositories/')) {
    return {
      data: {
        id: 104,
        full_name: 'shubham230523/Loom',
        name: 'Loom',
        description: 'AI-Powered Open-Source Contribution Platform',
        stars: 42,
        language: 'TypeScript',
        owner: { login: 'shubham230523', avatar_url: 'https://github.com/ghost.png' },
        loom_id: 'dummy-repo-123',
        is_imported: true,
      },
    };
  }

  // Default fallback object
  return { data: {} };
};

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response) {
      // The server responded with a status code outside 2xx range
      const apiError = error.response.data?.error;

      throw new ApiError(
        apiError?.message || 'An unexpected error occurred',
        apiError?.code || 'INTERNAL_ERROR',
        error.response.status,
        apiError?.details
      );
    } else if (error.request || error.code === 'ERR_NETWORK') {
      // Network error / server unreachable (e.g. static GitHub Pages demo or offline)
      const mockResult = getMockResponse(error.config?.url);
      if (mockResult) {
        return Promise.resolve(mockResult as any);
      }

      throw new ApiError(
        'Network error. Please check your connection.',
        'NETWORK_ERROR',
        0
      );
    } else {
      throw new ApiError(
        error.message || 'Request setup failed',
        'REQUEST_SETUP_ERROR',
        0
      );
    }
  }
);

export default apiClient;

