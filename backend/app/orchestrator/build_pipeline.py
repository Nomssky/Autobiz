"""Build pipeline — orchestrates agent tasks for a new business."""
from typing import Dict, List
from uuid import UUID
from datetime import datetime, timedelta

from app.models.business import Business
from app.models.agent_task import AgentTask
from app.models.approval_request import ApprovalRequest


def build_pipeline_tasks(
    business_id: UUID,
    idea: str,
    ceo_id: UUID,
) -> Dict[str, List[str]]:
    """
    Define the agent task pipeline for building a business.
    Returns task configs to be enqueued by Celery or executed inline.
    """
    tasks_config = {
        "research": {
            "role_name": "researcher",
            "task_type": "market_research",
            "input_data": {"idea": idea, "action": "competitor_and_market_analysis"},
            "priority": 5,
            "requires_approval": False,
        },
        "business_plan": {
            "role_name": "researcher",
            "task_type": "business_plan_generation",
            "input_data": {"idea": idea, "action": "generate_business_plan"},
            "priority": 4,
            "requires_approval": False,
        },
        "design": {
            "role_name": "designer",
            "task_type": "brand_and_ui_design",
            "input_data": {"idea": idea, "action": "generate_brand_identity"},
            "priority": 4,
            "requires_approval": True,
        },
        "development": {
            "role_name": "developer",
            "task_type": "application_generation",
            "input_data": {"idea": idea, "action": "generate_application_code"},
            "priority": 4,
            "requires_approval": True,
        },
        "marketing_strategy": {
            "role_name": "marketer",
            "task_type": "marketing_strategy",
            "input_data": {"idea": idea, "action": "create_go_to_market_plan"},
            "priority": 3,
            "requires_approval": False,
        },
        "financial_model": {
            "role_name": "finance",
            "task_type": "financial_modeling",
            "input_data": {"idea": idea, "action": "generate_financial_projections"},
            "priority": 3,
            "requires_approval": True,
        },
    }
    return tasks_config


def create_pipeline_approval(
    business_id: UUID,
    db_session,
) -> ApprovalRequest:
    """Create an approval request for the build pipeline budget."""
    approval = ApprovalRequest(
        business_id=business_id,
        title="Build Pipeline Budget Approval",
        description="Approve initial budget allocation for automated business build pipeline.",
        proposed_changes={
            "budget_usd": 5000,
            "scope": "full_build",
            "agents": ["researcher", "designer", "developer", "marketer", "finance"],
        },
        impact_analysis={
            "expected_roi": "variable",
            "risk": "medium",
            "time_to_complete": "24-48 hours",
        },
        urgency="high",
        status="pending",
        expires_at=datetime.utcnow() + timedelta(hours=48),
    )
    db_session.add(approval)
    db_session.flush()
    return approval


def run_build_pipeline(
    business_id: UUID,
    idea: str,
    db_session,
    ceo_id: UUID,
) -> Dict:
    """
    Execute the build pipeline for a new business.
    Creates tasks and approval requests, returns pipeline status.
    """
    tasks_config = build_pipeline_tasks(business_id, idea, ceo_id)
    created_tasks = []

    from app.models.agent_task import AgentTask

    for step_name, config in tasks_config.items():
        task = AgentTask(
            business_id=business_id,
            role_name=config["role_name"],
            task_type=config["task_type"],
            status="pending",
            input_data=config["input_data"],
            priority=config["priority"],
            requires_approval=config["requires_approval"],
        )
        db_session.add(task)
        created_tasks.append(task)

    db_session.flush()

    # Create a build approval request
    approval = create_pipeline_approval(business_id, db_session)

    # Link approval-required tasks to the approval
    for task in created_tasks:
        if task.requires_approval:
            task.approval_request_id = approval.id

    db_session.flush()

    return {
        "business_id": str(business_id),
        "tasks_created": len(created_tasks),
        "tasks_requiring_approval": sum(1 for t in created_tasks if t.requires_approval),
        "approval_request_id": str(approval.id),
        "final_phase": "tasks_created",
    }