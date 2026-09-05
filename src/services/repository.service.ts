import apiClient from './api-client';
import { SearchRepositoriesResponse, SearchParams, GitHubRepository } from '@/types/repository';

export class RepositoryService {
  static async search(params: SearchParams): Promise<SearchRepositoriesResponse> {
    const { data } = await apiClient.get<SearchRepositoriesResponse>('/api/v1/repositories/search', {
      params,
    });
    return data;
  }

  static async getById(id: number): Promise<GitHubRepository> {
    const { data } = await apiClient.get<GitHubRepository>(`/api/v1/repositories/${id}`);
    return data;
  }
}
