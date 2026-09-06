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
  test_runs?: TestRun[];
  code_reviews?: CodeReview[];
}

export interface TestRun {
  id: string;
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  status: 'success' | 'failure' | 'error';
  duration: number;
  timestamp: string;
}

export interface CodeReview {
  id: string;
  decision: 'APPROVE' | 'REQUEST_CHANGES' | 'REJECT';
  summary: string;
  review_issues: Array<{
    file_path?: string;
    line_number?: number;
    category: string;
    description: string;
    suggestion?: string;
    severity: string;
  }>;
  confidence: number;
  created_at: string;
}

export interface ValidationResult {
  is_valid: boolean;
  score: number;
  issues: Array<{
    category: string;
    severity: string;
    message: string;
    action_required: boolean;
  }>;
  summary: string;
}

export interface AgentRunResponse<T> {
  agent_run_id: string;
  plan?: T;
  result?: T;
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
