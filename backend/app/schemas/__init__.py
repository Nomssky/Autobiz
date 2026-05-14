from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class BusinessBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ceo_id: Optional[UUID] = None
    status: Optional[str] = "building"
    current_phase: Optional[str] = "initialization"
    metadata: Optional[dict] = {}



class BusinessCreate(BusinessBase):
    name: Optional[str] = None
    idea: str


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None
    metadata: Optional[dict] = None


class BusinessResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    ceo_id: UUID
    status: str
    current_phase: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    launched_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BusinessTimelineResponse(BaseModel):
    phases: list


# ---- Agent Task Schemas ----


class AgentTaskBase(BaseModel):
    business_id: UUID
    role_name: str
    task_type: str
    priority: int = 1
    input_data: Optional[dict] = None
    requires_approval: bool = False


class AgentTaskCreate(AgentTaskBase):
    pass


class AgentTaskUpdate(BaseModel):
    status: Optional[str] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    priority: Optional[int] = None
    approved_by_ceo_at: Optional[datetime] = None
    approval_request_id: Optional[UUID] = None


class AgentTaskResponse(BaseModel):
    id: UUID
    business_id: UUID
    role_name: str
    task_type: str
    status: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    priority: int
    requires_approval: bool
    approved_by_ceo_at: Optional[datetime] = None
    approval_request_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---- Approval Request Schemas ----


class ApprovalRequestBase(BaseModel):
    business_id: UUID
    title: str
    description: Optional[str] = None
    proposed_changes: dict
    impact_analysis: Optional[dict] = None
    urgency: str = "normal"


class ApprovalRequestCreate(ApprovalRequestBase):
    pass


class ApprovalRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    proposed_changes: Optional[dict] = None
    impact_analysis: Optional[dict] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    ceo_decision: Optional[str] = None
    decided_by_ceo_id: Optional[UUID] = None
    decided_at: Optional[datetime] = None


class ApprovalRequestResponse(BaseModel):
    id: UUID
    business_id: UUID
    task_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    proposed_changes: dict
    impact_analysis: Optional[dict] = None
    urgency: str
    status: str
    ceo_decision: Optional[str] = None
    decided_by_ceo_id: Optional[UUID] = None
    decided_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notification_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class ApprovalDecisionRequest(BaseModel):
    decision: ApprovalDecision
    ceo_id: UUID
    comments: Optional[str] = None


# ---- Deployment Schemas ----


class DeploymentBase(BaseModel):
    business_id: UUID
    version: str
    environment: str  # staging, production
    status: str = "pending"
    changes: Optional[dict] = None
    triggered_by_role: Optional[str] = None


class DeploymentCreate(DeploymentBase):
    pass


class DeploymentResponse(BaseModel):
    id: UUID
    business_id: UUID
    version: str
    environment: str
    status: str
    changes: Optional[dict] = None
    triggered_by_role: Optional[str] = None
    approved_by_ceo_id: Optional[UUID] = None
    deployed_at: Optional[datetime] = None
    rollback_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---- Metric Schema ----


class MetricSnapshotBase(BaseModel):
    business_id: UUID
    recorded_by_role: str
    daily_revenue: Optional[float] = None
    weekly_revenue: Optional[float] = None
    monthly_revenue: Optional[float] = None
    users_count: Optional[int] = None
    active_users_count: Optional[int] = None
    churn_rate: Optional[float] = None
    bug_count: Optional[int] = None
    support_tickets_count: Optional[int] = None
    open_support_tickets: Optional[int] = None
    conversion_rate: Optional[float] = None
    customer_acquisition_cost: Optional[float] = None
    lifetime_value: Optional[float] = None
    custom_metrics: Optional[dict] = None


class MetricSnapshotCreate(MetricSnapshotBase):
    pass


class MetricSnapshotResponse(BaseModel):
    id: UUID
    business_id: UUID
    recorded_by_role: str
    daily_revenue: Optional[float] = None
    weekly_revenue: Optional[float] = None
    monthly_revenue: Optional[float] = None
    users_count: Optional[int] = None
    active_users_count: Optional[int] = None
    churn_rate: Optional[float] = None
    bug_count: Optional[int] = None
    support_tickets_count: Optional[int] = None
    open_support_tickets: Optional[int] = None
    conversion_rate: Optional[float] = None
    customer_acquisition_cost: Optional[float] = None
    lifetime_value: Optional[float] = None
    custom_metrics: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- User Feedback Schema ----


class UserFeedbackBase(BaseModel):
    business_id: UUID
    user_id: Optional[str] = None
    feedback_type: Optional[str] = None  # bug, feature_request, praise, complaint
    content: str
    sentiment_score: Optional[float] = None  # -1 to 1


class UserFeedbackCreate(UserFeedbackBase):
    pass


class UserFeedbackResponse(BaseModel):
    id: UUID
    business_id: UUID
    user_id: Optional[str] = None
    feedback_type: Optional[str] = None
    content: str
    sentiment_score: Optional[float] = None
    processed_by_ai: bool = False
    processed_at: Optional[datetime] = None
    action_taken: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- Agent Execution Schema ----


class AgentExecutionBase(BaseModel):
    business_id: UUID
    role_name: str
    action: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    success: bool = True
    error: Optional[str] = None


class AgentExecutionCreate(AgentExecutionBase):
    pass


class AgentExecutionResponse(BaseModel):
    id: UUID
    business_id: UUID
    role_name: str
    action: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    success: bool = True
    error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- Metric (real-time response) ----

Timeframe = str  # hourly, daily, weekly, monthly


class RealtimeMetricsResponse(BaseModel):
    current: dict
    trends: dict
    alerts: list


# ---- Vector Memory Schemas (Sprint 8) ----


class VectorSearchRequest(BaseModel):
    business_id: UUID
    query: str
    top_k: int = 5


class VectorSearchResponse(BaseModel):
    query: str
    business_id: UUID
    results: List[dict]
    count: int


class VectorUpsertRequest(BaseModel):
    vectors: List[dict]


class KnowledgeEntryResponse(BaseModel):
    id: str
    source: str  # agent_task | user_feedback
    content: str
    role: str
    task_type: Optional[str] = None
    created_at: Optional[datetime] = None


# ---- Agent Feedback Schema (Sprint 8) ----


class AgentFeedbackRequest(BaseModel):
    business_id: UUID
    user_id: Optional[str] = None
    feedback_type: Optional[str] = None  # bug, feature_request, praise, complaint
    content: str
    sentiment_score: Optional[float] = None  # -1 to 1