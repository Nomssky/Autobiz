from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncio
import logging
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentResult
from app.orchestrator.crew_runner import CrewRunner

logger = logging.getLogger(__name__)


class TaskDistributor:
    """Distributes tasks to appropriate agents based on type and priority"""

    # Mapping of task types to agent roles
    TASK_ROUTING = {
        # Research tasks
        "validate_business_idea": "researcher",
        "market_analysis": "researcher",
        "competitor_research": "researcher",
        "trend_analysis": "researcher",

        # Development tasks
        "generate_application": "developer",
        "fix_bug": "developer",
        "implement_feature": "developer",
        "deploy": "developer",

        # Design tasks
        "generate_image": "designer",
        "create_logo": "designer",
        "design_banner": "designer",
        "edit_image": "designer",
        "create_brand_identity": "designer",

        # Marketing tasks
        "create_social_post": "marketer",
        "write_blog_post": "marketer",
        "create_email_campaign": "marketer",
        "analyze_performance": "marketer",
        "generate_hashtags": "marketer",
        "create_launch_strategy": "marketer",
        "activate_launch_campaigns": "marketer",
        "execute_scheduled_content": "marketer",
        "create_retention_campaign": "marketer",

        # Finance tasks
        "setup_pricing_and_payments": "finance",
        "setup_pricing": "finance",
        "setup_stripe_payments": "finance",
        "track_revenue": "finance",
        "calculate_unit_economics": "finance",
        "create_invoice": "finance",
        "generate_financial_projection": "finance",
        "get_current_metrics": "finance",
        "optimize_pricing": "finance",

        # Support tasks
        "process_ticket": "support",
        "auto_respond": "support",
        "escalate_ticket": "support",
        "search_knowledge_base": "support",
        "analyze_sentiment": "support",
        "generate_support_report": "support",
        "process_pending_tickets": "support",
    }

    # Priority queue configuration
    PRIORITY_LEVELS = {
        "critical": 5,
        "high": 4,
        "normal": 3,
        "low": 2,
        "background": 1
    }

    def __init__(self):
        self.task_queue: List[Dict[str, Any]] = []
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        self.failed_tasks: Dict[str, Dict[str, Any]] = {}
        self.pending_dependencies: Dict[str, List[str]] = {}
        self._processing = False

    def add_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        priority: str = "normal",
        depends_on: List[str] = None,
        context: Dict = None
    ) -> str:
        """Add a task to the distribution queue"""
        import uuid
        task_id = str(uuid.uuid4())

        agent_role = self.TASK_ROUTING.get(task_type)
        if not agent_role:
            logger.warning(f"No agent routing for task type: {task_type}")
            agent_role = "researcher"  # Default fallback

        task = {
            "task_id": task_id,
            "task_type": task_type,
            "agent_role": agent_role,
            "input_data": input_data,
            "priority": priority,
            "priority_score": self.PRIORITY_LEVELS.get(priority, 3),
            "depends_on": depends_on or [],
            "context": context or {},
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        self.task_queue.append(task)
        # Sort by priority (highest first)
        self.task_queue.sort(key=lambda t: t["priority_score"], reverse=True)

        if depends_on:
            for dep in depends_on:
                if dep not in self.pending_dependencies:
                    self.pending_dependencies[dep] = []
                self.pending_dependencies[dep].append(task_id)

        logger.info(f"Task {task_id} added: {task_type} -> {agent_role} (priority: {priority})")
        return task_id

    async def distribute_task(
        self,
        agent_pool: Dict[str, BaseAgent],
        task_type: str,
        input_data: Dict[str, Any],
        priority: str = "normal",
        context: Dict = None
    ) -> AgentResult:
        """Immediately distribute a task to the appropriate agent"""
        agent_role = self.TASK_ROUTING.get(task_type)

        if not agent_role:
            logger.warning(f"No agent routing for task type: {task_type}, using researcher as fallback")
            agent_role = "researcher"

        if agent_role not in agent_pool:
            return AgentResult(
                success=False,
                output=None,
                error=f"Agent {agent_role} not available in pool"
            )

        agent = agent_pool[agent_role]
        logger.info(f"Distributing task {task_type} to {agent_role}")

        try:
            result = await agent.run_with_tracking(task_type, input_data)
            task_id = self.add_task(task_type, input_data, priority, context=context)

            if result.success:
                self.completed_tasks[task_id] = {
                    "task_type": task_type,
                    "agent_role": agent_role,
                    "result": {
                        "success": result.success,
                        "output": result.output,
                        "execution_time_ms": result.execution_time_ms
                    }
                }
                # Check for dependent tasks
                await self._resolve_dependencies(task_id, agent_pool)
            else:
                self.failed_tasks[task_id] = {
                    "task_type": task_type,
                    "agent_role": agent_role,
                    "error": result.error
                }

            return result

        except Exception as e:
            logger.error(f"Task distribution failed for {task_type}: {str(e)}")
            return AgentResult(
                success=False,
                output=None,
                error=f"Task distribution failed: {str(e)}"
            )

    async def process_queue(
        self,
        agent_pool: Dict[str, BaseAgent],
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """Process all queued tasks"""
        self._processing = True
        results = {}
        processing = []

        while self.task_queue or processing:
            # Start new tasks up to max_concurrent
            while len(processing) < max_concurrent and self.task_queue:
                task = self.task_queue.pop(0)

                # Check if all dependencies are met
                deps_met = all(
                    dep in self.completed_tasks
                    for dep in task.get("depends_on", [])
                )
                if not deps_met:
                    # Put back and skip for now
                    self.task_queue.append(task)
                    break

                # Dispatch task
                coro = self._execute_task(agent_pool, task)
                processing.append(asyncio.create_task(coro))

            # Wait for at least one task to complete
            if processing:
                done, processing = await asyncio.wait(
                    processing, timeout=30, return_when=asyncio.FIRST_COMPLETED
                )
                for task_future in done:
                    task_id, result = task_future.result()
                    results[task_id] = result
            else:
                # No tasks processing but queue not empty — possible circular dependency
                logger.warning("Task queue stalled — possible circular dependency")
                break

        self._processing = False
        return {
            "results": results,
            "completed": len([r for r in results.values() if r.get("success")]),
            "failed": len([r for r in results.values() if not r.get("success")])
        }

    async def _execute_task(
        self,
        agent_pool: Dict[str, BaseAgent],
        task: Dict[str, Any]
    ) -> tuple:
        """Execute a single task"""
        task_id = task["task_id"]
        agent_role = task["agent_role"]

        try:
            agent = agent_pool.get(agent_role)
            if not agent:
                return task_id, {
                    "success": False,
                    "error": f"Agent {agent_role} not found"
                }

            result = await agent.run_with_tracking(
                task["task_type"],
                task["input_data"]
            )

            if result.success:
                self.completed_tasks[task_id] = result.output
                # Resolve dependent tasks
                await self._resolve_dependencies(task_id, agent_pool)
            else:
                self.failed_tasks[task_id] = result.error
                # Retry logic
                retry_count = task.get("retry_count", 0)
                if retry_count < 2:
                    task["retry_count"] = retry_count + 1
                    self.task_queue.append(task)
                    logger.info(f"Retrying task {task_id} (attempt {retry_count + 2})")

            return task_id, {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "requires_approval": result.requires_approval,
                "execution_time_ms": result.execution_time_ms
            }

        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            return task_id, {
                "success": False,
                "error": str(e)
            }

    async def _resolve_dependencies(self, completed_task_id: str, agent_pool: Dict[str, BaseAgent]):
        """Check and queue tasks whose dependencies are now met"""
        dependent_task_ids = self.pending_dependencies.pop(completed_task_id, [])
        for dep_task_id in dependent_task_ids:
            # Find the task in queue and check if all deps are met
            for task in self.task_queue:
                if task["task_id"] == dep_task_id:
                    deps_met = all(
                        dep in self.completed_tasks
                        for dep in task.get("depends_on", [])
                    )
                    if deps_met:
                        # Move to front of queue (high priority for unblocked tasks)
                        self.task_queue.remove(task)
                        task["priority_score"] += 1
                        self.task_queue.insert(0, task)
                        logger.info(f"Task {dep_task_id} unblocked by {completed_task_id}")
                        break

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "pending": len(self.task_queue),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "pending_task_ids": [t["task_id"] for t in self.task_queue],
            "is_processing": self._processing
        }
