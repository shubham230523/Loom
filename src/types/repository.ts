export interface GitHubRepository {
  id: number; // GitHub Integer ID
  loom_id?: string | null; // Loom UUID (optional/nullable)
  name: string;
  full_name: string;
  owner: {
    login: string;
    avatar_url: string;
  };
  html_url: string;
  description: string | null;
  stargazers_count: number;
  forks_count: number;
  language: string | null;
  default_branch: string;
  updated_at: string;
  is_imported?: boolean;
  indexing_status?: 'pending' | 'in_progress' | 'completed' | 'failed' | 'not_started' | null;
  discovery_status?: 'pending' | 'discovering' | 'completed' | 'failed' | null;
  discovery_error?: string | null;
}

export interface SearchRepositoriesResponse {
  total_count: number;
  incomplete_results: boolean;
  items: GitHubRepository[];
}

export interface SearchParams {
  q: string;
  language?: string;
  page?: number;
  per_page?: number;
}
