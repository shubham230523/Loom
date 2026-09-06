import apiClient from './api-client';
import { Opportunity, SyncOpportunitiesResponse } from '@/types/opportunity';

export class OpportunityService {
  static async list(repositoryId: string): Promise<Opportunity[]> {
    const { data } = await apiClient.get<Opportunity[]>(`/api/v1/repositories/${repositoryId}/opportunities`);
    return data;
  }

  static async getById(repositoryId: string, opportunityId: string): Promise<Opportunity> {
    const { data } = await apiClient.get<Opportunity>(`/api/v1/repositories/${repositoryId}/opportunities/${opportunityId}`);
    return data;
  }

  static async discover(repositoryId: string): Promise<SyncOpportunitiesResponse> {
    const { data } = await apiClient.post<SyncOpportunitiesResponse>(`/api/v1/repositories/${repositoryId}/opportunities/discover`);
    return data;
  }

  static async score(repositoryId: string, opportunityId: string): Promise<Opportunity> {
    const { data } = await apiClient.post<Opportunity>(`/api/v1/repositories/${repositoryId}/opportunities/${opportunityId}/score`);
    return data;
  }
}
