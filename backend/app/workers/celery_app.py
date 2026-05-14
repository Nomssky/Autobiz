import logging

from app.config import settings
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from kombu import Exchange, Queue

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
        "app.tasks.business_tasks",
        "app.tasks.agent_tasks",
        "app.tasks.batch_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=1800,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
    task_routes={
        "app.tasks.batch_tasks.batched_create_business": {"queue": "batch"},
        "app.tasks.batch_tasks.batched_metrics_aggregation": {"queue": "batch"},
        "app.tasks.business_tasks.*": {"queue": "business"},
        "app.tasks.agent_tasks.*": {"queue": "agent"},
    },
    task_queues=[
        Queue("critical", Exchange("critical"), routing_key="critical"),
        Queue("agent", Exchange("agent"), routing_key="agent"),
        Queue("business", Exchange("business"), routing_key="business"),
        Queue("batch", Exchange("batch"), routing_key="batch"),
    ],
    beat_schedule={
        "aggregate-metrics-every-5min": {
            "task": "app.tasks.batch_tasks.batched_metrics_aggregation",
            "schedule": 300.0,
            "options": {"queue": "batch"},
        },
        "cleanup-old-cache-every-hour": {
            "task": "app.tasks.batch_tasks.cache_cleanup",
            "schedule": 3600.0,
            "options": {"queue": "batch"},
        },
        "retry-failed-tasks-every-10min": {
            "task": "app.tasks.batch_tasks.retry_failed_tasks",
            "schedule": 600.0,
            "options": {"queue": "batch"},
        },
    },
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
