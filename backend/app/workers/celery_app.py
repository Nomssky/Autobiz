from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "autobiz_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.build_tasks",
        "app.workers.operate_tasks",
        "app.workers.monitoring_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,          # 1 hour max per task
    task_soft_time_limit=1800,     # 30 min soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    task_acks_late=True,           # Acknowledge after task completes
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    result_expires=3600,           # Results expire after 1 hour
)


@worker_ready.connect
def on_worker_ready(sender=None, conf=None, **kwargs):
    """Called when a Celery worker is ready"""
    logger.info("Celery worker is ready and connected to Redis broker")


@worker_shutdown.connect
def on_worker_shutdown(sender=None, conf=None, **kwargs):
    """Called when a Celery worker shuts down"""
    logger.info("Celery worker shutting down gracefully")


if __name__ == "__main__":
    celery_app.start()
