import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { ApiError, ApiErrorResponse } from '@/types/api';
import { useAuthStore } from '@/store/auth-store';

const DEFAULT_TIMEOUT = 15000; // 15 seconds

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

// Response Interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const apiError = error.response.data?.error;

      throw new ApiError(
        apiError?.message || 'An unexpected error occurred',
        apiError?.code || 'INTERNAL_ERROR',
        error.response.status,
        apiError?.details
      );
    } else if (error.request) {
      // The request was made but no response was received
      throw new ApiError(
        'Network error. Please check your connection.',
        'NETWORK_ERROR',
        0
      );
    } else {
      // Something happened in setting up the request that triggered an Error
      throw new ApiError(
        error.message || 'Request setup failed',
        'REQUEST_SETUP_ERROR',
        0
      );
    }
  }
);

export default apiClient;
