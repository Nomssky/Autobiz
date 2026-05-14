import asyncio
import logging
from uuid import UUID

from app.infrastructure.notification_service import NotificationService
from app.workers.celery_app import celery_app
from celery import Task

logger = logging.getLogger(__name__)


class OperateTask(Task):
    """Base task with error handling for operation tasks"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Operate task {task_id} failed: {str(exc)}")
        business_id = args[0] if args else None
        if business_id:
            notifier = NotificationService()
            try:
                asyncio.run(
                    notifier.send_system_alert(
                        "operation_failure",
                        f"Operation task failed for {business_id}: {str(exc)}",
                        severity="high",
                    )
                )
            except Exception:
                pass


@celery_app.task(bind=True, base=OperateTask, name="operate_tasks.continuous_support")
async def continuous_support(self, business_id: str, duration_seconds: int = 3600):
    """Run continuous support for a specified duration"""

    logger.info(f"Starting continuous support for {business_id} ({duration_seconds}s)")

    try:
        from app.agents.support import SupportAgent

        agent = SupportAgent(UUID(business_id), {})
        end_time = asyncio.get_event_loop().time() + duration_seconds
        processed = 0

        while asyncio.get_event_loop().time() < end_time:
            try:
                result = await agent.execute_task("process_pending_tickets", {"batch_size": 20})

                if result.success:
                    count = result.output.get("processed_count", 0)
                    processed += count
                    if count > 0:
                        logger.info(f"Support: processed {count} tickets in this cycle")

                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Continuous support error: {e}")
                await asyncio.sleep(300)

        logger.info(f"Continuous support completed: {processed} tickets processed")
        return {"status": "completed", "business_id": business_id, "tickets_processed": processed}

    except Exception as exc:
        logger.error(f"Continuous support failed for {business_id}: {exc}")
        raise self.retry(exc=exc, countdown=300, max_retries=5)


@celery_app.task(bind=True, base=OperateTask, name="operate_tasks.continuous_marketing")
async def continuous_marketing(self, business_id: str, duration_seconds: int = 7200):
    """Run continuous marketing for a specified duration"""

    logger.info(f"Starting continuous marketing for {business_id} ({duration_seconds}s)")

    try:
        from app.agents.marketer import MarketerAgent

        agent = MarketerAgent(UUID(business_id), {})
        end_time = asyncio.get_event_loop().time() + duration_seconds
        posts_created = 0

        while asyncio.get_event_loop().time() < end_time:
            try:
                result = await agent.execute_task("execute_scheduled_content", {})

                if result.success and result.output.get("posts_made", 0) > 0:
                    posts_created += result.output["posts_made"]
                    logger.info(f"Marketing: created {result.output['posts_made']} posts")

                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Continuous marketing error: {e}")
                await asyncio.sleep(3600)

        return {"status": "completed", "business_id": business_id, "posts_created": posts_created}

    except Exception as exc:
        logger.error(f"Continuous marketing failed for {business_id}: {exc}")
        raise self.retry(exc=exc, countdown=3600, max_retries=3)


@celery_app.task(name="operate_tasks.send_support_report")
async def send_support_report(business_id: str, period: str = "weekly"):
    """Generate and send a support report"""

    from app.agents.support import SupportAgent

    logger.info(f"Generating {period} support report for {business_id}")

    try:
        agent = SupportAgent(UUID(business_id), {})
        result = await agent.execute_task(
            "generate_support_report", {"period": period, "format": "summary"}
        )

        if result.success:
            return {"status": "completed", "business_id": business_id, "report": result.output}
        else:
            return {"status": "failed", "error": result.error}

    except Exception as exc:
        logger.error(f"Support report generation failed: {exc}")
        return {"status": "failed", "error": str(exc)}
