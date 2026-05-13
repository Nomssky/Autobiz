from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.api.dependencies import get_db_session, require_ceo
from app.models.approval_request import ApprovalRequest
from app.schemas import (
    ApprovalRequestCreate,
    ApprovalRequestUpdate,
    ApprovalRequestResponse,
    ApprovalDecisionRequest,
    ApprovalDecision,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get(
    "/",
    response_model=List[ApprovalRequestResponse],
    summary="List all approval requests",
)
def list_approvals(
    status_filter: Optional[str] = None,
    business_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """List all approval requests with optional filtering."""
    query = select(ApprovalRequest).order_by(desc(ApprovalRequest.created_at))

    if status_filter:
        query = query.where(ApprovalRequest.status == status_filter)
    if business_id:
        query = query.where(ApprovalRequest.business_id == business_id)

    query = query.offset(skip).limit(limit)
    result = db.execute(query)
    approvals = result.scalars().all()
    return [ApprovalRequestResponse.model_validate(a) for a in approvals]


@router.get(
    "/pending",
    response_model=List[ApprovalRequestResponse],
    summary="Get all pending approvals",
)
def get_pending_approvals(
    business_id: Optional[UUID] = None,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get all pending approval requests."""
    query = select(ApprovalRequest).where(ApprovalRequest.status == "pending")

    if business_id:
        query = query.where(ApprovalRequest.business_id == business_id)

    query = query.order_by(desc(ApprovalRequest.created_at)).limit(limit)
    result = db.execute(query)
    approvals = result.scalars().all()
    return [ApprovalRequestResponse.model_validate(a) for a in approvals]


@router.get(
    "/{approval_id}",
    response_model=ApprovalRequestResponse,
    summary="Get approval request details",
)
def get_approval(
    approval_id: UUID,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get details of a specific approval request."""
    result = db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    return ApprovalRequestResponse.model_validate(approval)


@router.post(
    "/",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an approval request",
)
def create_approval(
    request: ApprovalRequestCreate,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Create a new approval request for a business decision."""
    approval = ApprovalRequest(
        business_id=request.business_id,
        title=request.title,
        description=request.description,
        proposed_changes=request.proposed_changes or {},
        impact_analysis=request.impact_analysis,
        urgency=request.urgency,
        status="pending",
    )
    db.add(approval)
    db.flush()
    db.refresh(approval)
    return ApprovalRequestResponse.model_validate(approval)


@router.post(
    "/{approval_id}/decide",
    response_model=dict,
    summary="Submit CEO decision on approval",
)
def decide_approval(
    approval_id: UUID,
    decision: ApprovalDecisionRequest,
    db: Session = Depends(get_db_session),
    ceo_id: UUID = Depends(require_ceo),
):
    """Submit CEO decision (approve/reject) on an approval request."""
    result = db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

    if approval.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decide on approval with status '{approval.status}'; must be 'pending'",
        )

    now = datetime.utcnow()
    approval.status = decision.decision.value
    approval.ceo_decision = decision.comments
    approval.decided_by_ceo_id = ceo_id
    approval.decided_at = now
    approval.updated_at = now

    db.flush()

    return {
        "approval_id": str(approval_id),
        "approved": decision.decision == ApprovalDecision.APPROVE,
        "message": f"Decision '{decision.decision.value}' recorded successfully",
    }


@router.patch(
    "/{approval_id}",
    response_model=ApprovalRequestResponse,
    summary="Update approval request",
)
def update_approval(
    approval_id: UUID,
    updates: ApprovalRequestUpdate,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Update an approval request."""
    result = db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(approval, field, value)

    approval.updated_at = datetime.utcnow()
    db.flush()
    db.refresh(approval)
    return ApprovalRequestResponse.model_validate(approval)


@router.delete(
    "/{approval_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an approval request",
)
def cancel_approval(
    approval_id: UUID,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Cancel/expire an approval request."""
    result = db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

    if approval.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel approval with status '{approval.status}'",
        )

    approval.status = "cancelled"
    approval.updated_at = datetime.utcnow()
    db.flush()
    return