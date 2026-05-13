// AutoBiz Engine — TypeScript Type Definitions

export interface UUID {
  _uuid: string;
}

export interface Business {
  id: string;
  name: string;
  description: string | null;
  ceo_id: string;
  status: 'building' | 'operating' | 'archived' | 'failed';
  current_phase: string;
  created_at: string;
  updated_at?: string;
  launched_at?: string;
  archived_at?: string;
  metadata?: Record<string, any>;
}

export interface BusinessCreatePayload {
  idea: string;
  ceo_id: string;
}

export interface BusinessTimelineResponse {
  phases: PhaseTask[];
}

export interface PhaseTask {
  task_id: string;
  role_name: string;
  task_type: string;
  status: string;
  priority: number;
  created_at: string | null;
  completed_at: string | null;
}

export interface ApprovalRequest {
  id: string;
  business_id: string;
  task_id: string | null;
  title: string;
  description: string | null;
  proposed_changes: Record<string, any>;
  impact_analysis: Record<string, any> | null;
  urgency: 'low' | 'normal' | 'high' | 'critical';
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  ceo_decision: string | null;
  decided_by_ceo_id: string | null;
  decided_at: string | null;
  expires_at: string | null;
  notification_sent_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ApprovalDecisionRequest {
  decision: 'approve' | 'reject';
  ceo_id: string;
  comments?: string;
}

export interface MetricSnapshot {
  id: string;
  business_id: string;
  recorded_by_role: string;
  daily_revenue: number | null;
  weekly_revenue: number | null;
  monthly_revenue: number | null;
  users_count: number | null;
  active_users_count: number | null;
  churn_rate: number | null;
  bug_count: number | null;
  support_tickets_count: number | null;
  open_support_tickets: number | null;
  conversion_rate: number | null;
  customer_acquisition_cost: number | null;
  lifetime_value: number | null;
  custom_metrics: Record<string, any> | null;
  created_at: string;
}

export interface MetricSnapshotCreatePayload {
  business_id: string;
  recorded_by_role: string;
  daily_revenue?: number;
  weekly_revenue?: number;
  monthly_revenue?: number;
  users_count?: number;
  active_users_count?: number;
  churn_rate?: number;
  bug_count?: number;
  support_tickets_count?: number;
  open_support_tickets?: number;
  conversion_rate?: number;
  customer_acquisition_cost?: number;
  lifetime_value?: number;
  custom_metrics?: Record<string, any>;
}

export interface RealtimeMetricsResponse {
  current: {
    revenue: number;
    users: number;
    active_users: number;
    bugs: number;
    support_tickets: number;
  };
  trends: {
    revenue_growth: number;
    user_growth: number;
    churn_rate: number;
  };
  alerts: Alert[];
}

export interface Alert {
  type: 'warning' | 'error' | 'info';
  message: string;
}

export interface VectorSearchRequest {
  business_id: string;
  query: string;
  top_k?: number;
}

export interface VectorSearchResponse {
  query: string;
  business_id: string;
  results: VectorResult[];
  count: number;
}

export interface VectorResult {
  id: string;
  score: number;
  payload: Record<string, any>;
}

export interface KnowledgeEntry {
  id: string;
  source: string;
  content: string;
  role: string;
  task_type?: string;
  created_at?: string;
}

export interface AgentFeedbackPayload {
  business_id: string;
  user_id?: string;
  feedback_type?: string;
  content: string;
  sentiment_score?: number;
}

export interface AgentEvaluation {
  role_name: string;
  score: number | null;
  grade: string;
  total_executions: number;
  success_rate: number;
  avg_cost_usd: number;
  avg_duration_ms: number;
  avg_tokens: number;
  trend: 'improving' | 'stable' | 'declining';
  suggestions: Suggestion[];
}

export interface Suggestion {
  area: string;
  priority: 'high' | 'medium' | 'low' | 'info';
  suggestion: string;
  impact: string;
}

export interface AgentTask {
  id: string;
  business_id: string;
  role_name: string;
  task_type: string;
  status: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  priority: number;
  requires_approval: boolean;
  started_at?: string;
  completed_at?: string;
}