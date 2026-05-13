"""
Database Indexing Migration
Adds missing indexes to improve query performance for the AutoBiz Engine.
Run with: alembic revision --autogenerate -m "add_performance_indexes"
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "perf_indexes_v1"
down_revision = "c960424bfc03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Business table indexes
    op.create_index(
        "idx_businesses_ceo_id",
        "businesses",
        ["ceo_id"],
        unique=False,
    )
    op.create_index(
        "idx_businesses_status",
        "businesses",
        ["status"],
        unique=False,
    )
    op.create_index(
        "idx_businesses_current_phase",
        "businesses",
        ["current_phase"],
        unique=False,
    )
    op.create_index(
        "idx_businesses_status_ceo",
        "businesses",
        ["status", "ceo_id"],
        unique=False,
    )
    op.create_index(
        "idx_businesses_created_at",
        "businesses",
        ["created_at"],
        unique=False,
    )

    # Agent tasks indexes
    op.create_index(
        "idx_agent_tasks_business_id",
        "ai_tasks",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "idx_agent_tasks_status",
        "ai_tasks",
        ["status"],
        unique=False,
    )
    op.create_index(
        "idx_agent_tasks_role_status",
        "ai_tasks",
        ["role_name", "status"],
        unique=False,
    )
    op.create_index(
        "idx_agent_tasks_priority",
        "ai_tasks",
        ["priority"],
        unique=False,
    )
    op.create_index(
        "idx_agent_tasks_business_status",
        "ai_tasks",
        ["business_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_agent_tasks_created_at",
        "ai_tasks",
        ["created_at"],
        unique=False,
    )

    # Approval requests indexes
    op.create_index(
        "idx_approvals_business_id",
        "approval_requests",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "idx_approvals_status",
        "approval_requests",
        ["status"],
        unique=False,
    )
    op.create_index(
        "idx_approvals_urgency",
        "approval_requests",
        ["urgency"],
        unique=False,
    )
    op.create_index(
        "idx_approvals_status_urgency",
        "approval_requests",
        ["status", "urgency"],
        unique=False,
    )
    op.create_index(
        "idx_approvals_business_status",
        "approval_requests",
        ["business_id", "status"],
        unique=False,
    )

    # Metrics snapshots indexes
    op.create_index(
        "idx_metrics_business_id",
        "metrics_snapshots",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "idx_metrics_recorded_by_role",
        "metrics_snapshots",
        ["recorded_by_role"],
        unique=False,
    )
    op.create_index(
        "idx_metrics_business_created",
        "metrics_snapshots",
        ["business_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_metrics_created_at",
        "metrics_snapshots",
        ["created_at"],
        unique=False,
    )

    # Agent executions indexes
    op.create_index(
        "idx_executions_business_id",
        "agent_executions",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "idx_executions_role_name",
        "agent_executions",
        ["role_name"],
        unique=False,
    )
    op.create_index(
        "idx_executions_created_at",
        "agent_executions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "idx_executions_business_role",
        "agent_executions",
        ["business_id", "role_name"],
        unique=False,
    )

    # User feedback indexes
    op.create_index(
        "idx_feedback_business_id",
        "user_feedback",
        ["business_id"],
        unique=False,
    )
    op.create_index(
        "idx_feedback_created_at",
        "user_feedback",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_feedback_created_at", table_name="user_feedback")
    op.drop_index("idx_feedback_business_id", table_name="user_feedback")
    op.drop_index("idx_executions_business_role", table_name="agent_executions")
    op.drop_index("idx_executions_created_at", table_name="agent_executions")
    op.drop_index("idx_executions_role_name", table_name="agent_executions")
    op.drop_index("idx_executions_business_id", table_name="agent_executions")
    op.drop_index("idx_metrics_created_at", table_name="metrics_snapshots")
    op.drop_index("idx_metrics_business_created", table_name="metrics_snapshots")
    op.drop_index("idx_metrics_recorded_by_role", table_name="metrics_snapshots")
    op.drop_index("idx_metrics_business_id", table_name="metrics_snapshots")
    op.drop_index("idx_approvals_business_status", table_name="approval_requests")
    op.drop_index("idx_approvals_status_urgency", table_name="approval_requests")
    op.drop_index("idx_approvals_urgency", table_name="approval_requests")
    op.drop_index("idx_approvals_status", table_name="approval_requests")
    op.drop_index("idx_approvals_business_id", table_name="approval_requests")
    op.drop_index("idx_agent_tasks_created_at", table_name="ai_tasks")
    op.drop_index("idx_agent_tasks_business_status", table_name="ai_tasks")
    op.drop_index("idx_agent_tasks_priority", table_name="ai_tasks")
    op.drop_index("idx_agent_tasks_role_status", table_name="ai_tasks")
    op.drop_index("idx_agent_tasks_status", table_name="ai_tasks")
    op.drop_index("idx_agent_tasks_business_id", table_name="ai_tasks")
    op.drop_index("idx_businesses_created_at", table_name="businesses")
    op.drop_index("idx_businesses_status_ceo", table_name="businesses")
    op.drop_index("idx_businesses_current_phase", table_name="businesses")
    op.drop_index("idx_businesses_status", table_name="businesses")
    op.drop_index("idx_businesses_ceo_id", table_name="businesses")