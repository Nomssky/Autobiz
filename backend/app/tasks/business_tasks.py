"""
Business-related background tasks (Celery workers).
"""

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_business_creation(self, business_data: dict):
    """
    Process business creation asynchronously.
    Used when immediate processing isn't required.
    """
    try:
        from app.database import SessionLocal
        from app.models.business import Business
        from sqlalchemy.orm import Session

        db: Session = SessionLocal()
        try:
            business = Business(
                name=business_data["name"][:255],
                description=business_data.get("description", ""),
                ceo_id=business_data["ceo_id"],
                status="building",
                current_phase="initialization",
                metadata=business_data.get("metadata", {}),
            )
            db.add(business)
            db.flush()
            db.refresh(business)
            db.commit()
            return {"business_id": str(business.id), "status": "created"}
        finally:
            db.close()

    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2)
def update_business_metrics(self, business_id: str):
    """
    Refresh metrics for a business.
    """
    try:
        from app.api.v1.metrics import get_metric_summary
        from app.database import SessionLocal
        from sqlalchemy.orm import Session

        db: Session = SessionLocal()
        try:
            # This will use the Redis cache layer if available
            summary = get_metric_summary(business_id=business_id, db=db, days=7)
            return {"business_id": business_id, "summary": summary}
        finally:
            db.close()

    except Exception as exc:
        raise self.retry(exc=exc)
