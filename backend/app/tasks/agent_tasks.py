"""
Agent-related background tasks (Celery workers).
"""

from celery import current_app


@current_app.task(bind=True, max_retries=3, default_retry_delay=120)
async def run_agent_task(self, task_id: str, task_type: str, input_data: dict):
    """
    Execute an agent task asynchronously with retry logic.
    """
    try:
        from app.orchestrator.task_distributor import TaskDistributor

        distributor = TaskDistributor()
        result = await distributor.distribute_task(
            agent_pool={},  # Injected by the running worker
            task_type=task_type,
            input_data=input_data,
        )
        return {"task_id": task_id, "success": result.success, "output": result.output}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=min(self.request.retries * 60, 600))


@current_app.task(bind=True, max_retries=2)
def run_batch_agent_tasks(self, tasks: list[dict]):
    """
    Run multiple agent tasks in a batch.
    """
    results = []
    for task in tasks:
        try:
            run_agent_task.apply(
                args=(task["task_id"], task["task_type"], task["input_data"]),
                priority=task.get("priority", 3),
            )
            results.append({"task_id": task["task_id"], "queued": True})
        except Exception as e:
            results.append({"task_id": task["task_id"], "error": str(e)})

    return results
