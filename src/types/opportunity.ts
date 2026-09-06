export type OpportunityType = 'bug' | 'feature' | 'refactor' | 'documentation' | 'testing';
export type ImpactLevel = 'Low' | 'Medium' | 'High';
export type DifficultyLevel = 'Easy' | 'Intermediate' | 'Hard';

export interface Opportunity {
  id: string;
  repository_id: string;
  issue_id?: string;
  title: string;
  description: string;
  type: OpportunityType;
  impact: ImpactLevel;
  difficulty: DifficultyLevel;
  confidence: number;
  score: number;
  status: 'pending' | 'started' | 'completed' | 'failed';
  scoring_reasoning?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SyncOpportunitiesResponse {
  status: string;
  new_opportunities_count: number;
}
