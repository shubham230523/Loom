import apiClient from './api-client';
import { Contribution, SolutionPlan } from '@/types/contribution';

export class ContributionService {
  static async start(repositoryId: string, opportunityId: string): Promise<Contribution> {
    const { data } = await apiClient.post<Contribution>(`/api/v1/repositories/${repositoryId}/contributions`, null, {
      params: { opportunity_id: opportunityId }
    });
    return data;
  }

  static async generatePlan(repositoryId: string, contributionId: string): Promise<SolutionPlan> {
    const { data } = await apiClient.post<SolutionPlan>(`/api/v1/repositories/${repositoryId}/contributions/${contributionId}/plan`);
    return data;
  }

  static async approvePlan(repositoryId: string, planId: string, approved: boolean = true): Promise<SolutionPlan> {
    const { data } = await apiClient.post<SolutionPlan>(`/api/v1/repositories/${repositoryId}/plans/${planId}/approve`, null, {
      params: { approved }
    });
    return data;
  }
}
