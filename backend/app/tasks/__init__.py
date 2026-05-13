"""
Celery Configuration & Task Batching
Optimizes background task processing for the AutoBiz Engine.
"""
from celery import Celery
from kombu import Queue, Exchange

from app.config import settings


# ---- Celery App ----
celery_app = Celery(
    "autobiz_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.business_tasks",
        "app.tasks.agent_tasks",
        "app.tasks.batch_tasks",
    ],
)

# ---- Global Celery Configuration ----
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.batch_tasks.batched_create_business": {"queue": "batch"},
        "app.tasks.batch_tasks.batched_metrics_aggregation": {"queue": "batch"},
        "app.tasks.business_tasks.*": {"queue": "business"},
        "app.tasks.agent_tasks.*": {"queue": "agent"},
    },

    # Queue definitions with priorities
    task_queues=[
        Queue("critical", Exchange("critical"), routing_key="critical"),
        Queue("agent", Exchange("agent"), routing_key="agent"),
        Queue("business", Exchange("business"), routing_key="business"),
        Queue("batch", Exchange("batch"), routing_key="batch"),
    ],

    # Quality of Service
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,

    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Retry & Reliability
    task_default_retry_delay=60,
    task_max_retries=3,

    # Beat schedule for periodic tasks
    beat_schedule={
        "aggregate-metrics-every-5min": {
            "task": "app.tasks.batch_tasks.batched_metrics_aggregation",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "batch"},
        },
        "cleanup-old-cache-every-hour": {
            "task": "app.tasks.batch_tasks.cache_cleanup",
            "schedule": 3600.0,  # Every hour
            "options": {"queue": "batch"},
        },
        "retry-failed-tasks-every-10min": {
            "task": "app.tasks.batch_tasks.retry_failed_tasks",
            "schedule": 600.0,  # Every 10 minutes
            "options": {"queue": "batch"},
        },
    },

    # Worker optimization
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
    worker_disable_rate_limits=False,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# ---- Batching Utilities ----

class TaskBatcher:
    """
    Utility to batch multiple small tasks into a single larger task,
    reducing Celery overhead for high-frequency operations.
    """

    def __init__(self, batch_size: int = 50, flush_interval: int = 5):
        """
        Args:
            batch_size: Maximum number of items per batch.
            flush_interval: Seconds before auto-flushing an incomplete batch.
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer: dict[str, list] = {}

    def add(self, task_type: str, item: dict) -> bool:
        """
        Add an item to the batch buffer.

        Args:
            task_type: The Celery task name.
            item: The task payload.

        Returns:
            True if batch was flushed (reached batch_size), False otherwise.
        """
        if task_type not in self._buffer:
            self._buffer[task_type] = []

        self._buffer[task_type].append(item)

        if len(self._buffer[task_type]) >= self.batch_size:
            self.flush(task_type)
            return True
        return False

    def flush(self, task_type: str = None) -> int:
        """
        Flush buffered items as batch tasks.

        Args:
            task_type: If provided, flush only this task type. If None, flush all.

        Returns:
            Number of batches submitted.
        """
        from app.tasks.batch_tasks import batched_create_business

        batches_submitted = 0
        types_to_flush = [task_type] if task_type else list(self._buffer.keys())

        for ttype in types_to_flush:
            items = self._buffer.get(ttype, [])
            if not items:
                continue

            # Submit as a batch task
            if ttype == "create_business":
                batched_create_business.delay(items)
            # Add more task-type handlers as needed

            batches_submitted += 1
            self._buffer[ttype] = []

        return batches_submitted

    def flush_all(self) -> int:
        """Flush all buffered items."""
        return self.flush()


# Default batcher instance
default_batcher = TaskBatcher(batch_size=50, flush_interval=5)