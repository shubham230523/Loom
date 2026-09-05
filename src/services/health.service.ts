import apiClient from './api-client';

export interface HealthStatus {
  status: string;
  app_name: string;
  environment: string;
  version: string;
}

export const getHealth = async (): Promise<HealthStatus> => {
  const response = await apiClient.get<HealthStatus>('/api/v1/health');
  return response.data;
};
