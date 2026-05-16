import asyncio
import logging
from uuid import UUID

from app.agents.finance import FinanceAgent
from app.agents.support import SupportAgent
from app.approval.notifier import ApprovalNotifier
from app.workers.celery_app import celery_app
from celery import Task

logger = logging.getLogger(__name__)


class MonitoringTask(Task):
    """Base task with error handling for monitoring operations"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Monitoring task {task_id} failed: {str(exc)}")


@celery_app.task(bind=True, base=MonitoringTask, name="monitoring_tasks.monitor_business_metrics")
def monitor_business_metrics(self, business_id: str):
    logger.info(f"Monitoring metrics for business {business_id}")

    async def _run():
        agent = FinanceAgent(UUID(business_id), {})
        result = await agent.execute_task("get_current_metrics", {})

        if not result.success:
            return {"status": "failed", "error": result.error}

        metrics = result.output
        alerts = []

        if metrics.get("revenue_change_percent", 0) < -20:
            alerts.append(f"Revenue dropped {abs(metrics['revenue_change_percent'])}%")

        if metrics.get("churn_rate", 0) > 0.1:
            alerts.append(f"High churn rate: {metrics['churn_rate'] * 100}%")

        if metrics.get("bug_count", 0) > 10:
            alerts.append(f"Bug spike: {metrics['bug_count']} active bugs")

        if alerts:
            notifier = ApprovalNotifier()
            for alert in alerts:
                await notifier.send_system_alert(
                    "metric_anomaly", f"Business {business_id}: {alert}", severity="critical"
                )

        return {
            "status": "monitored",
            "business_id": business_id,
            "metrics_summary": {
                "daily_revenue": metrics.get("daily_revenue"),
                "active_users": metrics.get("active_users_count"),
                "churn_rate": metrics.get("churn_rate"),
                "bugs": metrics.get("bug_count"),
            },
            "alerts": alerts,
        }

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Metrics monitoring failed for {business_id}: {exc}")
        raise self.retry(exc=exc, countdown=300, max_retries=3)


@celery_app.task(bind=True, base=MonitoringTask, name="monitoring_tasks.monitor_support_quality")
def monitor_support_quality(self, business_id: str):
    logger.info(f"Monitoring support quality for {business_id}")

    async def _run():
        agent = SupportAgent(UUID(business_id), {})
        result = await agent.execute_task(
            "generate_support_report", {"period": "daily", "format": "summary"}
        )

        if not result.success:
            return {"status": "failed", "error": result.error}

        report = result.output
        alerts = []

        if report.get("metrics", {}).get("ticket_volume", {}).get("new_tickets", 0) > 100:
            alerts.append("High ticket volume detected")

        avg_resolution = (
            report.get("metrics", {}).get("resolution_time", {}).get("avg_resolution_hours", 0)
        )
        if avg_resolution > 8:
            alerts.append(f"Slow resolution time: {avg_resolution}h average")

        csat = report.get("metrics", {}).get("customer_satisfaction", {}).get("csat_score", 5)
        if csat < 3.5:
            alerts.append(f"Low customer satisfaction: {csat}/5")

        if alerts:
            notifier = ApprovalNotifier()
            for alert in alerts:
                await notifier.send_system_alert(
                    "support_quality", f"Business {business_id}: {alert}", severity="high"
                )

        return {
            "status": "monitored",
            "business_id": business_id,
            "support_metrics": report.get("metrics", {}),
            "alerts": alerts,
        }

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Support monitoring failed for {business_id}: {exc}")
        raise self.retry(exc=exc, countdown=600, max_retries=2)


@celery_app.task(name="monitoring_tasks.health_check")
def health_check():
    """System-wide health check"""
    logger.info("Running system health check")

    checks = {"celery": True, "redis": False, "database": False}

    try:
        import redis as redis_lib
        from app.config import settings

        r = redis_lib.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = True
    except Exception as e:
        logger.warning(f"Health check — Redis unavailable: {e}")

    try:
        from app.database import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(engine.dialect.text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.warning(f"Health check — database unavailable: {e}")

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }
