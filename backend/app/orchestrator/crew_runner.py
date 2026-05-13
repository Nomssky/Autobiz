from typing import Dict, Any, List, Optional
from uuid import UUID
import asyncio
import logging
from datetime import datetime

from app.agents.base_agent import BaseAgent, AgentResult
from app.agents.researcher import ResearcherAgent
from app.agents.developer import DeveloperAgent
from app.agents.designer import DesignerAgent
from app.agents.marketer import MarketerAgent
from app.agents.finance import FinanceAgent
from app.agents.support import SupportAgent
from app.config import settings

logger = logging.getLogger(__name__)


class CrewRunner:
    """Manages crew-based agent execution for build and operate phases"""

    def __init__(self, business_id: UUID):
        self.business_id = business_id
        self.crew: Dict[str, BaseAgent] = {}
        self.execution_log: List[Dict[str, Any]] = []

    async def initialize_crew(self, config: Dict[str, Any] = None):
        """Initialize all agents in the crew"""
        if config is None:
            config = {}

        self.crew = {
            "researcher": ResearcherAgent(self.business_id, config.get("researcher", {})),
            "developer": DeveloperAgent(self.business_id, config.get("developer", {})),
            "designer": DesignerAgent(self.business_id, config.get("designer", {})),
            "marketer": MarketerAgent(self.business_id, config.get("marketer", {})),
            "finance": FinanceAgent(self.business_id, config.get("finance", {})),
            "support": SupportAgent(self.business_id, config.get("support", {}))
        }
        logger.info(f"Crew initialized with {len(self.crew)} agents for business {self.business_id}")

    async def run_crew(
        self,
        tasks: List[Dict[str, Any]],
        max_parallel: int = 3
    ) -> Dict[str, Any]:
        """Execute a list of tasks using available crew members"""
        results = {}
        errors = []

        for i, task in enumerate(tasks):
            agent_role = task.get("agent_role")
            task_type = task.get("task_type")
            input_data = task.get("input_data", {})
            depends_on = task.get("depends_on", [])

            # Check dependencies
            if depends_on:
                for dep in depends_on:
                    if dep not in results or not results[dep].get("success"):
                        logger.warning(f"Task {i} skipped: dependency {dep} not met")
                        results[f"task_{i}"] = {
                            "success": False,
                            "skipped": True,
                            "reason": f"Dependency {dep} not met"
                        }
                        continue

            # Check if agent is available
            if agent_role not in self.crew:
                logger.error(f"Agent {agent_role} not found in crew")
                results[f"task_{i}"] = {
                    "success": False,
                    "error": f"Agent {agent_role} not available"
                }
                continue

            # Execute task
            try:
                agent = self.crew[agent_role]
                result = await agent.run_with_tracking(task_type, input_data)
                task_id = f"task_{i}"
                results[task_id] = {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "requires_approval": result.requires_approval,
                    "approval_proposal": result.approval_proposal,
                    "execution_time_ms": result.execution_time_ms,
                    "agent_role": agent_role,
                    "task_type": task_type
                }

                self.execution_log.append({
                    "task_id": task_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_role": agent_role,
                    "task_type": task_type,
                    "success": result.success,
                    "duration_ms": result.execution_time_ms
                })

                logger.info(f"Task {i} ({agent_role}.{task_type}): {'success' if result.success else 'failed'}")

            except Exception as e:
                logger.error(f"Task {i} execution error: {str(e)}")
                results[f"task_{i}"] = {
                    "success": False,
                    "error": str(e)
                }
                errors.append({"task_index": i, "error": str(e)})

        return {
            "results": results,
            "errors": errors,
            "total_tasks": len(tasks),
            "successful": sum(1 for r in results.values() if r.get("success")),
            "failed": sum(1 for r in results.values() if not r.get("success"))
        }

    async def run_phase(
        self,
        phase_name: str,
        tasks: List[Dict[str, Any]],
        auto_approve_routine: bool = True
    ) -> Dict[str, Any]:
        """Run all tasks in a specific phase"""
        logger.info(f"Starting crew phase: {phase_name}")

        result = await self.run_crew(tasks)

        # Handle approvals for tasks that need them
        tasks_needing_approval = [
            (tid, t) for tid, t in result["results"].items()
            if t.get("requires_approval") and t.get("approval_proposal")
        ]

        if tasks_needing_approval and auto_approve_routine:
            from app.approval.gateway import approval_gateway
            from app.models import AgentTask

            for task_id, task_result in tasks_needing_approval:
                try:
                    proposal = task_result["approval_proposal"]
                    # Auto-approve low-impact tasks
                    impact = proposal.get("impact", "").lower()
                    if "minor" in impact or "small" in impact or len(impact) < 10:
                        approval_id = await approval_gateway.create_approval_request(
                            self.business_id,
                            None,
                            proposal,
                            urgency="low"
                        )
                        await approval_gateway.process_decision(
                            approval_id,
                            self.business_id,  # Using business_id as placeholder
                            "approve",
                            "Auto-approved: low impact task"
                        )
                        logger.info(f"Auto-approved task: {task_id}")
                except Exception as e:
                    logger.error(f"Auto-approval failed for {task_id}: {e}")

        return result

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the full execution log for this crew run"""
        return self.execution_log

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents in the crew"""
        status = {}
        for role, agent in self.crew.items():
            tools = agent.get_tools()
            status[role] = {
                "role_name": agent.role_name,
                "business_id": str(agent.business_id),
                "tools_count": len(tools),
                "tools": [t.get("name") if isinstance(t, dict) else getattr(t, "name", "?") for t in tools],
                "memory_entries": len(agent.memory) if hasattr(agent, "memory") else 0
            }
        return status
