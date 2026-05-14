import logging
from uuid import UUID

from app.approval.notifier import ApprovalNotifier
from app.orchestrator.phase_manager import PhaseManager
from app.workers.celery_app import celery_app
from celery import Task

logger = logging.getLogger(__name__)


class BuildTask(Task):
    """Base task with error handling for build operations"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Build task {task_id} failed: {str(exc)}")
        business_id = args[0] if args else None
        if business_id:
            notifier = ApprovalNotifier()
            try:
                import asyncio

                asyncio.run(
                    notifier.send_system_alert(
                        "build_failure",
                        f"Build process failed for business {business_id}: {str(exc)}",
                        severity="critical",
                    )
                )
            except Exception:
                pass


@celery_app.task(bind=True, base=BuildTask, name="build_tasks.build_business")
async def build_business(self, business_id: str, idea: str):
    """Celery task for building a business from an idea"""

    logger.info(f"Starting build task for business {business_id}")

    try:
        phase_manager = PhaseManager(UUID(business_id))
        await phase_manager.initialize_agents()
        result = await phase_manager.execute_build_phase(idea)

        if result["success"]:
            logger.info(f"Build completed for {business_id}")
            # Start operate phase as a separate task
            operate_business.delay(business_id)
        else:
            logger.error(f"Build failed for {business_id}: {result.get('error')}")

        return {
            "status": "success" if result["success"] else "failed",
            "business_id": business_id,
            "phases_completed": list(result.get("phases", {}).keys()),
            "error": result.get("error"),
            "business_url": result.get("business_url"),
        }

    except Exception as exc:
        logger.error(f"Build task exception for {business_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True, base=BuildTask, name="build_tasks.operate_business")
async def operate_business(self, business_id: str):
    """Celery task for starting the operate phase"""

    logger.info(f"Starting operate phase for {business_id}")

    try:
        phase_manager = PhaseManager(UUID(business_id))
        await phase_manager.initialize_agents()
        result = await phase_manager.execute_operate_phase()

        return {
            "status": "operating",
            "business_id": business_id,
            "operations_running": result.get("operations_running", 0),
        }

    except Exception as exc:
        logger.error(f"Operate task exception for {business_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=120, max_retries=2)


@celery_app.task(name="build_tasks.process_phase_approvals")
async def process_phase_approvals(business_id: str):
    """Process any pending approvals for a business"""

    from app.approval.gateway import approval_gateway

    logger.info(f"Processing approvals for business {business_id}")

    try:
        await approval_gateway.auto_handle_routine(UUID(business_id))
        return {"status": "completed", "business_id": business_id}
    except Exception as exc:
        logger.error(f"Approval processing failed for {business_id}: {exc}")
        return {"status": "failed", "business_id": business_id, "error": str(exc)}
