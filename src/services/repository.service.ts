import apiClient from './api-client';
import { SearchRepositoriesResponse, SearchParams, GitHubRepository } from '@/types/repository';

export class RepositoryService {
  static async search(params: SearchParams): Promise<SearchRepositoriesResponse> {
    const { data } = await apiClient.get<SearchRepositoriesResponse>('/api/v1/repositories/search', {
      params,
    });
    return data;
  }

  static async getById(id: string): Promise<GitHubRepository & { loom_id: string | null; is_imported: boolean }> {
    const { data } = await apiClient.get(`/api/v1/repositories/${id}`);
    return data;
  }

  static async initialize(githubId: number): Promise<GitHubRepository & { id: string }> {
    const { data } = await apiClient.post('/api/v1/repositories/initialize', null, {
      params: { github_id: githubId },
    });
    return data;
  }
}
