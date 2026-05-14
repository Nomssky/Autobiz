"""
Batch processing tasks for the AutoBiz Engine.
Handles high-volume operations that benefit from batching.
"""

from datetime import datetime

from celery import current_app


@current_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="app.tasks.batch_tasks.batched_create_business",
)
def batched_create_business(self, business_items: list[dict]):
    """
    Create multiple businesses in a single database transaction.

    Args:
        business_items: List of dicts with keys: name, description, ceo_id, metadata.
    """
    try:
        from app.database import SessionLocal
        from app.models.business import Business
        from sqlalchemy.orm import Session

        db: Session = SessionLocal()
        try:
            created = []
            for item in business_items:
                business = Business(
                    name=item["name"][:255],
                    description=item.get("description", ""),
                    ceo_id=item["ceo_id"],
                    status="building",
                    current_phase="initialization",
                    metadata=item.get("metadata", {}),
                )
                db.add(business)
                db.flush()
                db.refresh(business)
                created.append({"business_id": str(business.id), "name": business.name})

            db.commit()
            return {
                "batch_size": len(business_items),
                "created": len(created),
                "businesses": created,
                "timestamp": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()

    except Exception as exc:
        raise self.retry(exc=exc)


@current_app.task(
    bind=True,
    max_retries=2,
    name="app.tasks.batch_tasks.batched_metrics_aggregation",
)
def batched_metrics_aggregation(self):
    """
    Aggregate metrics across all businesses and store summary results.
    Runs every 5 minutes via Celery Beat.
    """
    try:
        from app.database import SessionLocal
        from app.models.metric import MetricSnapshot
        from sqlalchemy import func
        from sqlalchemy.orm import Session

        db: Session = SessionLocal()
        try:
            # Aggregate metrics by role
            role_stats = (
                db.query(
                    MetricSnapshot.recorded_by_role,
                    func.count(MetricSnapshot.id).label("count"),
                    func.avg(MetricSnapshot.daily_revenue).label("avg_revenue"),
                    func.avg(MetricSnapshot.users_count).label("avg_users"),
                    func.avg(MetricSnapshot.churn_rate).label("avg_churn"),
                )
                .group_by(MetricSnapshot.recorded_by_role)
                .all()
            )

            # Aggregate metrics by business
            business_stats = (
                db.query(
                    MetricSnapshot.business_id,
                    func.count(MetricSnapshot.id).label("snapshot_count"),
                    func.max(MetricSnapshot.created_at).label("latest"),
                    func.avg(MetricSnapshot.daily_revenue).label("avg_revenue"),
                )
                .group_by(MetricSnapshot.business_id)
                .all()
            )

            result = {
                "aggregation_timestamp": datetime.utcnow().isoformat(),
                "by_role": [
                    {
                        "role": r.recorded_by_role,
                        "count": r.count,
                        "avg_revenue": float(r.avg_revenue) if r.avg_revenue else 0,
                        "avg_users": float(r.avg_users) if r.avg_users else 0,
                        "avg_churn": float(r.avg_churn) if r.avg_churn else 0,
                    }
                    for r in role_stats
                ],
                "businesses_tracked": len(business_stats),
            }

            # Store in Redis cache for quick dashboard access
            try:
                from app.infrastructure.cache import get_redis

                redis = get_redis()
                if redis:
                    redis.setex(
                        "metrics:aggregation:latest",
                        300,  # 5 min TTL
                        __import__("json").dumps(result, default=str),
                    )
            except Exception:
                pass

            return result
        finally:
            db.close()

    except Exception as exc:
        raise self.retry(exc=exc)


@current_app.task(
    bind=True,
    name="app.tasks.batch_tasks.cache_cleanup",
)
def cache_cleanup(self):
    """
    Clean up expired and stale cache entries.
    Runs every hour via Celery Beat.
    """
    try:
        from app.infrastructure.cache import get_redis

        redis = get_redis()
        if not redis:
            return {"status": "skipped", "reason": "no redis"}

        # Clean up orphaned rate limiter entries
        rate_keys = redis.keys("rate_limit:*")
        if rate_keys:
            redis.delete(*rate_keys)

        return {
            "status": "completed",
            "rate_limit_keys_cleaned": len(rate_keys),
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@current_app.task(
    bind=True,
    max_retries=3,
    name="app.tasks.batch_tasks.retry_failed_tasks",
)
def retry_failed_tasks(self):
    """
    Periodic task to retry any failed business processing tasks.
    Runs every 10 minutes via Celery Beat.
    """
    try:
        from datetime import timedelta

        from app.database import SessionLocal
        from app.models.agent_task import AgentTask
        from sqlalchemy import select
        from sqlalchemy.orm import Session

        db: Session = SessionLocal()
        try:
            # Find tasks stuck in 'running' for too long (stale > 30 minutes)
            stale_threshold = datetime.utcnow() - timedelta(minutes=30)
            result = db.execute(
                select(AgentTask)
                .where(AgentTask.status == "running")
                .where(AgentTask.updated_at < stale_threshold)
            )
            stale_tasks = result.scalars().all()

            retried = 0
            for task in stale_tasks:
                task.status = "pending"
                task.retry_count = (task.retry_count or 0) + 1
                logger.info(
                    f"Retrying stale task {task.id} ({task.task_type}) — "
                    f"attempt {task.retry_count}"
                )
                retried += 1

            db.commit()

            return {
                "status": "completed",
                "stale_tasks_found": len(stale_tasks),
                "retried": retried,
                "timestamp": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()

    except Exception as exc:
        raise self.retry(exc=exc)
