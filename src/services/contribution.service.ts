import apiClient from './api-client';
import { Contribution, SolutionPlan, AgentRunResponse } from '@/types/contribution';

export class ContributionService {
  static async start(repositoryId: string, opportunityId: string): Promise<Contribution> {
    const { data } = await apiClient.post<Contribution>(`/api/v1/repositories/${repositoryId}/contributions`, null, {
      params: { opportunity_id: opportunityId }
    });
    return data;
  }

  static async getDetails(repositoryId: string, contributionId: string): Promise<Contribution> {
    const { data } = await apiClient.get<Contribution>(`/api/v1/repositories/${repositoryId}/contributions/${contributionId}`);
    return data;
  }

  static async generatePlan(repositoryId: string, contributionId: string): Promise<AgentRunResponse<SolutionPlan>> {
    const { data } = await apiClient.post<AgentRunResponse<SolutionPlan>>(`/api/v1/repositories/${repositoryId}/contributions/${contributionId}/plan`);
    return data;
  }

  static async approvePlan(repositoryId: string, planId: string, approved: boolean = true): Promise<SolutionPlan> {
    const { data } = await apiClient.post<SolutionPlan>(`/api/v1/repositories/${repositoryId}/plans/${planId}/approve`, null, {
      params: { approved }
    });
    return data;
  }

  static async setupWorkspace(repositoryId: string, contributionId: string): Promise<{ workspace_id: string, path: string }> {
    const { data } = await apiClient.post<{ workspace_id: string, path: string }>(`/api/v1/repositories/${repositoryId}/contributions/${contributionId}/workspace`);
    return data;
  }

  static async executeImplementation(repositoryId: string, contributionId: string): Promise<AgentRunResponse<any>> {
    const { data } = await apiClient.post<AgentRunResponse<any>>(`/api/v1/repositories/${repositoryId}/contributions/${contributionId}/implement`);
    return data;
  }

  static async validate(repositoryId: string, contributionId: string): Promise<any> {
    const { data } = await apiClient.get<any>(`/api/v1/repositories/${repositoryId}/contributions/${contributionId}/validate`);
    return data;
  }

  static async push(repositoryId: string, contributionId: string): Promise<{ status: string, branch: string, repository: string }> {
    const { data } = await apiClient.post<{ status: string, branch: string, repository: string }>(`/api/v1/repositories/${repositoryId}/contributions/${contributionId}/push`);
    return data;
  }

  static async createPullRequest(repositoryId: string, contributionId: string): Promise<{ id: number, number: number, url: string, title: string }> {
    const { data } = await apiClient.post<{ id: number, number: number, url: string, title: string }>(`/api/v1/repositories/${repositoryId}/contributions/${contributionId}/pull-request`);
    return data;
  }
}
