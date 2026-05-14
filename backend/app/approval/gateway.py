import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from app.approval.notifier import ApprovalNotifier
from app.database import SessionLocal
from app.models import AgentTask, ApprovalRequest, Business
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ApprovalGateway:
    """Manages CEO approval workflow for major decisions"""

    def __init__(self):
        self.notifier = ApprovalNotifier()

    def get_db(self) -> Session:
        return SessionLocal()

    async def create_approval_request(
        self, business_id: UUID, task_id: UUID, proposal: Dict[str, Any], urgency: str = "normal"
    ) -> UUID:
        """Create a new approval request"""
        db = self.get_db()
        try:
            # Calculate expiry based on urgency
            expiry_hours = {"critical": 4, "high": 12, "normal": 48, "low": 168}.get(  # 1 week
                urgency, 48
            )

            approval = ApprovalRequest(
                id=uuid4(),
                business_id=business_id,
                task_id=task_id,
                title=proposal.get("title", "Untitled Approval Request"),
                description=proposal.get("description", ""),
                proposed_changes=proposal,
                impact_analysis=proposal.get("impact_analysis", {}),
                urgency=urgency,
                status="pending",
                expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
            )

            db.add(approval)
            db.commit()

            # Send notification to CEO
            approval_dict = {
                "id": str(approval.id),
                "business_id": str(approval.business_id),
                "task_id": str(approval.task_id) if approval.task_id else None,
                "title": approval.title,
                "description": approval.description,
                "proposed_changes": approval.proposed_changes or {},
                "impact_analysis": approval.impact_analysis or {},
                "urgency": approval.urgency,
                "status": approval.status,
                "expires_at": approval.expires_at.isoformat() if approval.expires_at else None,
                "created_at": approval.created_at.isoformat() if approval.created_at else None,
            }
            await self.notifier.notify_ceo(approval_dict)

            return approval.id
        finally:
            db.close()

    async def process_decision(
        self,
        approval_id: UUID,
        ceo_id: UUID,
        decision: str,  # "approve", "reject"
        comments: Optional[str] = None,
    ) -> bool:
        """Process CEO's decision on approval request"""
        db = self.get_db()
        try:
            approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
            if not approval:
                raise ValueError(f"Approval request {approval_id} not found")

            if approval.status != "pending":
                raise ValueError(f"Approval request already {approval.status}")

            if datetime.utcnow() > approval.expires_at:
                approval.status = "expired"
                db.commit()
                raise ValueError("Approval request has expired")

            # Update approval record
            approval.status = "approved" if decision == "approve" else "rejected"
            approval.decided_by_ceo_id = ceo_id
            approval.ceo_decision = comments
            approval.decided_at = datetime.utcnow()

            # Update associated task
            if approval.task_id:
                task = db.query(AgentTask).filter(AgentTask.id == approval.task_id).first()
                if task:
                    task.approved_by_ceo_at = datetime.utcnow()
                    if decision == "approve":
                        task.status = "approved"
                    else:
                        task.status = "rejected"

            db.commit()

            # Notify agent about decision
            await self._notify_agent(str(approval.id), decision)

            return decision == "approve"
        finally:
            db.close()

    async def get_pending_approvals(self, ceo_id: UUID, limit: int = 50) -> list[Dict[str, Any]]:
        """Get all pending approval requests for a CEO"""
        db = self.get_db()
        try:

            query = (
                db.query(ApprovalRequest)
                .join(Business, ApprovalRequest.business_id == Business.id)
                .filter(Business.ceo_id == ceo_id, ApprovalRequest.status == "pending")
                .order_by(ApprovalRequest.urgency.desc(), ApprovalRequest.created_at.asc())
                .limit(limit)
            )

            approvals = query.all()

            return [
                {
                    "id": str(a.id),
                    "business_id": str(a.business_id),
                    "title": a.title,
                    "description": a.description,
                    "proposed_changes": a.proposed_changes,
                    "urgency": a.urgency,
                    "expires_at": a.expires_at.isoformat(),
                    "created_at": a.created_at.isoformat(),
                }
                for a in approvals
            ]
        finally:
            db.close()

    async def auto_handle_routine(self, business_id: UUID) -> None:
        """Auto-approve routine tasks based on rules"""
        db = self.get_db()
        try:
            from app.models import AgentTask

            # Find tasks that can be auto-approved
            tasks = (
                db.query(AgentTask)
                .filter(
                    AgentTask.business_id == business_id,
                    AgentTask.requires_approval.is_(True),
                    AgentTask.approval_request_id.is_(None),
                    AgentTask.status == "completed",
                )
                .all()
            )

            for task in tasks:
                # Check if this task qualifies for auto-approval
                if await self._should_auto_approve(task):
                    # Create auto-approval
                    approval = ApprovalRequest(
                        id=uuid4(),
                        business_id=business_id,
                        task_id=task.id,
                        title=f"Auto-approved: {task.task_type}",
                        proposed_changes=task.output_data or {},
                        status="approved",
                        decided_at=datetime.utcnow(),
                    )
                    db.add(approval)
                    task.approved_by_ceo_at = datetime.utcnow()
                    task.status = "approved"

            db.commit()
        finally:
            db.close()

    async def _should_auto_approve(self, task: AgentTask) -> bool:
        """Determine if task can be auto-approved based on rules"""

        # Load auto-approval rules
        auto_approve_types = [
            "performance_optimization",
            "security_patch",
            "bug_fix_critical",
            "typo_fix",
            "documentation_update",
        ]

        if task.task_type in auto_approve_types:
            return True

        # Check impact threshold
        impact = task.output_data.get("impact", {})
        user_impact = impact.get("users_affected", 0)
        revenue_impact = abs(impact.get("revenue_change_percent", 0))

        if user_impact < 100 and revenue_impact < 5:
            return True

        return False

    async def _notify_agent(self, approval_id: str, decision: str) -> None:
        """Notify the agent about the decision"""
        await self.notifier.notify_agent(approval_id, decision)


approval_gateway = ApprovalGateway()
