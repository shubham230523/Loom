export interface Contribution {
  id: string;
  user_id: string;
  repository_id: string;
  opportunity_id: string;
  status: 'started' | 'in_progress' | 'pull_request_created' | 'merged' | 'failed';
  branch_name?: string;
  created_at: string;
  updated_at: string;
  solution_plan?: SolutionPlan;
  diff_summary?: {
    diff: string;
    stats: string;
    files: string[];
    additions: number;
    deletions: number;
  };
}

export interface SolutionPlan {
  id: string;
  contribution_id: string;
  problem: string;
  root_cause: string;
  relevant_files: string[];
  relevant_symbols: string[];
  implementation_steps: string[];
  testing_strategy: string;
  risks: string;
  expected_diff_size: string;
  confidence: number;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  updated_at: string;
}
