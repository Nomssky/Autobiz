from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.api.dependencies import get_db_session, require_ceo
from app.models.metric import MetricSnapshot
from app.models.business import Business
from app.schemas import (
    MetricSnapshotCreate,
    MetricSnapshotResponse,
    RealtimeMetricsResponse,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/",
    response_model=List[MetricSnapshotResponse],
    summary="List all metric snapshots",
)
def list_metrics(
    business_id: Optional[UUID] = None,
    recorded_by_role: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """List all metric snapshots with optional filtering."""
    query = select(MetricSnapshot).order_by(desc(MetricSnapshot.created_at))

    if business_id:
        query = query.where(MetricSnapshot.business_id == business_id)
    if recorded_by_role:
        query = query.where(MetricSnapshot.recorded_by_role == recorded_by_role)

    query = query.offset(skip).limit(limit)
    result = db.execute(query)
    metrics = result.scalars().all()
    return [MetricSnapshotResponse.model_validate(m) for m in metrics]


@router.get(
    "/{metric_id}",
    response_model=MetricSnapshotResponse,
    summary="Get metric snapshot details",
)
def get_metric(
    metric_id: UUID,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get details of a specific metric snapshot."""
    result = db.execute(
        select(MetricSnapshot).where(MetricSnapshot.id == metric_id)
    )
    metric = result.scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric snapshot not found")
    return MetricSnapshotResponse.model_validate(metric)


@router.get(
    "/{business_id}/realtime",
    response_model=RealtimeMetricsResponse,
    summary="Get real-time business metrics",
)
def get_realtime_metrics(
    business_id: UUID,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get real-time business metrics for a specific business."""
    result = db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    latest_result = db.execute(
        select(MetricSnapshot)
        .where(MetricSnapshot.business_id == business_id)
        .order_by(desc(MetricSnapshot.created_at))
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()

    if latest:
        current = {
            "revenue": float(latest.daily_revenue) if latest.daily_revenue else 0.0,
            "users": latest.users_count or 0,
            "active_users": latest.active_users_count or 0,
            "bugs": latest.bug_count or 0,
            "support_tickets": latest.support_tickets_count or 0,
        }
        trends = {
            "revenue_growth": 0.0,
            "user_growth": 0.0,
            "churn_rate": float(latest.churn_rate) if latest.churn_rate else 0.0,
        }
    else:
        current = {
            "revenue": 0.0,
            "users": 0,
            "active_users": 0,
            "bugs": 0,
            "support_tickets": 0,
        }
        trends = {
            "revenue_growth": 0.0,
            "user_growth": 0.0,
            "churn_rate": 0.0,
        }

    alerts = []
    if current["bugs"] > 5:
        alerts.append({"type": "warning", "message": "High bug count detected"})
    if current["support_tickets"] > 20:
        alerts.append({"type": "warning", "message": "High support ticket volume"})

    return RealtimeMetricsResponse(current=current, trends=trends, alerts=alerts)


@router.get(
    "/{business_id}/summary",
    response_model=dict,
    summary="Get metric summary for a business",
)
def get_metric_summary(
    business_id: UUID,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get aggregated metric summary for a business over a time period."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = db.execute(
        select(
            func.count(MetricSnapshot.id).label("snapshot_count"),
            func.avg(MetricSnapshot.daily_revenue).label("avg_daily_revenue"),
            func.max(MetricSnapshot.daily_revenue).label("max_daily_revenue"),
            func.avg(MetricSnapshot.users_count).label("avg_users"),
            func.avg(MetricSnapshot.active_users_count).label("avg_active_users"),
            func.avg(MetricSnapshot.bug_count).label("avg_bugs"),
            func.avg(MetricSnapshot.churn_rate).label("avg_churn_rate"),
        )
        .where(MetricSnapshot.business_id == business_id)
        .where(MetricSnapshot.created_at >= cutoff)
    )
    row = result.first()

    if row.snapshot_count == 0:
        return {
            "business_id": str(business_id),
            "period_days": days,
            "message": "No metric data available for this period",
        }

    return {
        "business_id": str(business_id),
        "period_days": days,
        "snapshot_count": row.snapshot_count,
        "avg_daily_revenue": float(row.avg_daily_revenue) if row.avg_daily_revenue else 0.0,
        "max_daily_revenue": float(row.max_daily_revenue) if row.max_daily_revenue else 0.0,
        "avg_users": round(float(row.avg_users), 2) if row.avg_users else 0,
        "avg_active_users": round(float(row.avg_active_users), 2) if row.avg_active_users else 0,
        "avg_bugs": round(float(row.avg_bugs), 2) if row.avg_bugs else 0,
        "avg_churn_rate": float(row.avg_churn_rate) if row.avg_churn_rate else 0.0,
    }


@router.post(
    "/",
    response_model=MetricSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a metric snapshot",
)
def create_metric(
    request: MetricSnapshotCreate,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Create a new metric snapshot for a business."""
    result = db.execute(
        select(Business).where(Business.id == request.business_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    metric = MetricSnapshot(
        business_id=request.business_id,
        recorded_by_role=request.recorded_by_role,
        daily_revenue=request.daily_revenue,
        weekly_revenue=request.weekly_revenue,
        monthly_revenue=request.monthly_revenue,
        users_count=request.users_count,
        active_users_count=request.active_users_count,
        churn_rate=request.churn_rate,
        bug_count=request.bug_count,
        support_tickets_count=request.support_tickets_count,
        open_support_tickets=request.open_support_tickets,
        conversion_rate=request.conversion_rate,
        customer_acquisition_cost=request.customer_acquisition_cost,
        lifetime_value=request.lifetime_value,
        custom_metrics=request.custom_metrics,
    )
    db.add(metric)
    db.flush()
    db.refresh(metric)
    return MetricSnapshotResponse.model_validate(metric)


@router.delete(
    "/{metric_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a metric snapshot",
)
def delete_metric(
    metric_id: UUID,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Delete a metric snapshot."""
    result = db.execute(
        select(MetricSnapshot).where(MetricSnapshot.id == metric_id)
    )
    metric = result.scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric snapshot not found")

    db.delete(metric)
    db.flush()
    return