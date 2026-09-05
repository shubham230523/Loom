import apiClient from './api-client';
import { SearchRepositoriesResponse, SearchParams } from '@/types/repository';

export class RepositoryService {
  static async search(params: SearchParams): Promise<SearchRepositoriesResponse> {
    const { data } = await apiClient.get<SearchRepositoriesResponse>('/api/v1/repositories/search', {
      params,
    });
    return data;
  }
}
