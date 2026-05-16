import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.api.dependencies import get_db_session, require_ceo
from app.config import settings
from app.models.agent_task import AgentTask
from app.models.business import Business
from app.orchestrator.build_pipeline import run_build_pipeline
from app.schemas import BusinessCreate, BusinessResponse, BusinessTimelineResponse, BusinessUpdate
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

logger = logging.getLogger(__name__)


def _check_ownership(business: Business, ceo_id: UUID):
    if str(business.ceo_id) != str(ceo_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the business owner can perform this action",
        )


def _validate_llm_config():
    provider = (settings.LLM_PROVIDER or "").lower()
    has_api_key = bool(settings.LLM_API_KEY or settings.OPENAI_API_KEY)
    if provider != "ollama" and not has_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "LLM is not configured. Set LLM_API_KEY in Settings or "
                "switch to LLM_PROVIDER=ollama for local models."
            ),
        )


router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new business",
)
def create_business(
    request: BusinessCreate,
    db: Session = Depends(get_db_session),
    ceo_id: UUID = Depends(require_ceo),
):
    """Create a new business from an idea and trigger the build pipeline."""
    _validate_llm_config()

    business = Business(
        name=request.idea[:255],
        description=request.idea,
        ceo_id=ceo_id,
        status="building",
        current_phase="initialization",
        metadata={},
    )
    db.add(business)
    db.flush()
    db.refresh(business)

    try:
        pipeline_result = run_build_pipeline(business.id, request.idea, db, ceo_id)
        business.current_phase = pipeline_result.get("final_phase", "tasks_created")
        business.updated_at = datetime.utcnow()
        db.flush()
    except Exception as e:
        business.status = "failed"
        business.updated_at = datetime.utcnow()
        db.flush()
        logger.error(f"Pipeline failed for business {business.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline gagal: {str(e)}",
        )

    # Agent warnings berdasarkan model saat ini
    from app.agents.registry import check_warnings, classify_model
    model_name = settings.LLM_MODEL or settings.OPENAI_MODEL or ""
    model_info = classify_model(model_name) if model_name else {"tier": "unknown"}
    warnings = check_warnings({}, model_info.get("tier", "unknown"))

    response = BusinessResponse.model_validate(business).model_dump()
    response["agent_warnings"] = warnings
    return response


@router.get(
    "/",
    response_model=List[BusinessResponse],
    summary="List all businesses",
)
def list_businesses(
    status_filter: Optional[str] = None,
    ceo_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """List all businesses with optional filtering by status and CEO."""
    query = (
        select(Business).options(selectinload(Business.tasks)).order_by(desc(Business.created_at))
    )

    if status_filter:
        query = query.where(Business.status == status_filter)
    if ceo_id:
        query = query.where(Business.ceo_id == ceo_id)

    query = query.offset(skip).limit(limit)
    result = db.execute(query)
    businesses = result.scalars().all()
    return [BusinessResponse.model_validate(b) for b in businesses]


@router.get(
    "/{business_id}",
    response_model=BusinessResponse,
    summary="Get business details",
)
def get_business(
    business_id: UUID,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get business details and current status."""
    query = select(Business).options(selectinload(Business.tasks)).where(Business.id == business_id)
    result = db.execute(query)
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return BusinessResponse.model_validate(business)


@router.patch(
    "/{business_id}",
    response_model=BusinessResponse,
    summary="Update business",
)
def update_business(
    business_id: UUID,
    updates: BusinessUpdate,
    db: Session = Depends(get_db_session),
    ceo_id: UUID = Depends(require_ceo),
):
    """Update business details (only owner can update)."""
    result = db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    _check_ownership(business, ceo_id)

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(business, field, value)

    business.updated_at = datetime.utcnow()
    db.flush()
    db.refresh(business)
    return BusinessResponse.model_validate(business)


@router.delete(
    "/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a business",
)
def archive_business(
    business_id: UUID,
    db: Session = Depends(get_db_session),
    ceo_id: UUID = Depends(require_ceo),
):
    """Archive a business (soft delete). Only the owner can archive."""
    result = db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    _check_ownership(business, ceo_id)

    business.status = "archived"
    business.archived_at = datetime.utcnow()
    business.updated_at = datetime.utcnow()
    db.flush()
    return


@router.get(
    "/{business_id}/timeline",
    response_model=BusinessTimelineResponse,
    summary="Get business build timeline",
)
def get_business_timeline(
    business_id: UUID,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get build and operation timeline for a business."""
    result = db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    tasks_result = db.execute(
        select(AgentTask).where(AgentTask.business_id == business_id).order_by(AgentTask.created_at)
    )
    tasks = tasks_result.scalars().all()

    phases = [
        {
            "task_id": str(t.id),
            "role_name": t.role_name,
            "task_type": t.task_type,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]

    return BusinessTimelineResponse(phases=phases)


@router.post(
    "/{business_id}/launch",
    response_model=BusinessResponse,
    summary="Launch a business",
)
def launch_business(
    business_id: UUID,
    db: Session = Depends(get_db_session),
    ceo_id: UUID = Depends(require_ceo),
):
    """Launch a business, transitioning it from building to operating."""
    result = db.execute(select(Business).where(Business.id == business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    _check_ownership(business, ceo_id)

    if business.status != "building":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot launch business in status '{business.status}'; must be 'building'",
        )

    business.status = "operating"
    business.launched_at = datetime.utcnow()
    business.current_phase = "operation"
    business.updated_at = datetime.utcnow()
    db.flush()
    db.refresh(business)
    return BusinessResponse.model_validate(business)
