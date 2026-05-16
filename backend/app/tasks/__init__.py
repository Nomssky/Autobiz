"""
Task batching utilities for the AutoBiz Engine.
Celery app is defined in app.workers.celery_app.
"""


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
