"""Prompt optimizer — auto-refines prompts based on success rate tracking."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """Analyzes agent execution history and optimizes prompts."""

    def __init__(self, db_session):
        self.db = db_session

    def get_execution_stats(
        self,
        business_id: UUID,
        role_name: Optional[str] = None,
        days: int = 30,
    ) -> Dict:
        """Get execution statistics for optimization insights."""
        from app.models.agent_execution import AgentExecution
        from sqlalchemy import desc, select

        cutoff = datetime.utcnow() - timedelta(days=days)

        query = (
            select(AgentExecution)
            .where(AgentExecution.business_id == business_id)
            .where(AgentExecution.created_at >= cutoff)
        )

        if role_name:
            query = query.where(AgentExecution.role_name == role_name)

        query = query.order_by(desc(AgentExecution.created_at))
        result = self.db.execute(query)
        executions = result.scalars().all()

        if not executions:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_cost": 0.0,
                "avg_duration_ms": 0,
                "avg_tokens": 0,
            }

        total = len(executions)
        success_count = sum(1 for e in executions if e.success)

        return {
            "total_executions": total,
            "success_count": success_count,
            "failure_count": total - success_count,
            "success_rate": round(success_count / total, 4),
            "avg_cost_usd": round(sum(e.cost_usd or 0 for e in executions) / total, 4),
            "avg_duration_ms": round(sum(e.duration_ms or 0 for e in executions) / total, 1),
            "avg_input_tokens": round(sum(e.input_tokens or 0 for e in executions) / total, 1),
            "avg_output_tokens": round(sum(e.output_tokens or 0 for e in executions) / total, 1),
        }

    def analyze_failures(self, business_id: UUID, role_name: Optional[str] = None) -> List[Dict]:
        """Analyze failed executions to identify improvement patterns."""
        from app.models.agent_execution import AgentExecution
        from sqlalchemy import desc, select

        query = (
            select(AgentExecution)
            .where(AgentExecution.business_id == business_id)
            .where(AgentExecution.success.is_(False))
            .order_by(desc(AgentExecution.created_at))
            .limit(50)
        )

        if role_name:
            query = query.where(AgentExecution.role_name == role_name)

        result = self.db.execute(query)
        failures = result.scalars().all()

        error_patterns = {}
        for f in failures:
            error = f.error or "unknown"
            # Normalize error patterns
            key = self._categorize_error(error)
            error_patterns.setdefault(key, {"count": 0, "examples": []})
            error_patterns[key]["count"] += 1
            if len(error_patterns[key]["examples"]) < 3:
                error_patterns[key]["examples"].append(error[:200])

        return [{"pattern": pattern, **stats} for pattern, stats in error_patterns.items()]

    def generate_optimized_prompt(
        self,
        original_prompt: str,
        role_name: str,
        business_context: Dict,
        execution_stats: Dict,
    ) -> str:
        """Generate an optimized version of a prompt based on execution history.

        In production, this would use an LLM to rewrite the prompt.
        Here, we apply heuristic-based improvements.
        """
        optimizations = []

        # If success rate is low for this role, add clearer instructions
        if execution_stats.get("success_rate", 1.0) < 0.7:
            optimizations.append(
                "[CLEARER_INSTRUCTIONS]: Provide step-by-step reasoning "
                "and validate all outputs before returning."
            )

        # If cost is high, add token efficiency instruction
        avg_cost = execution_stats.get("avg_cost_usd", 0)
        if avg_cost > 0.1:
            optimizations.append(
                "[TOKEN_EFFICIENT]: Be concise. Avoid unnecessary repetition. "
                "Use structured output (JSON) when possible."
            )

        # If duration is high, add complexity reduction
        avg_duration = execution_stats.get("avg_duration_ms", 0)
        if avg_duration > 5000:
            optimizations.append(
                "[SIMPLIFY]: Break complex tasks into smaller subtasks. "
                "Return intermediate results."
            )

        # If output is too long, add length constraints
        avg_output = execution_stats.get("avg_output_tokens", 0)
        if avg_output > 2000:
            optimizations.append(
                "[LENGTH_LIMIT]: Keep response under 1000 tokens. " "Summarize key findings only."
            )

        if optimizations:
            optimized = (
                "You are an optimized agent. Follow these improvement directives:\n"
                + "\n".join(optimizations)
                + "\n\n"
                + original_prompt
            )
            logger.info(
                f"Prompt optimized for {role_name}: {len(optimizations)} optimizations applied"
            )
            return optimized

        return original_prompt

    def _categorize_error(self, error: str) -> str:
        """Categorize an error message into a pattern group."""
        error_lower = error.lower()

        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "rate_limit" in error_lower or "rate limit" in error_lower or "429" in error:
            return "rate_limit"
        elif "invalid" in error_lower or "validation" in error_lower:
            return "invalid_input"
        elif "auth" in error_lower or "permission" in error_lower or "unauthorized" in error_lower:
            return "authentication"
        elif "network" in error_lower or "connection" in error_lower:
            return "network"
        elif "memory" in error_lower or "context" in error_lower:
            return "context_overflow"
        else:
            return "unknown_error"
