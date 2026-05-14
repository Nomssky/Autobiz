"""Success evaluator — measures agent decision quality over time."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import UUID

logger = logging.getLogger(__name__)


class SuccessEvaluator:
    """Evaluates agent execution quality and suggests improvements."""

    # Scoring weights (tunable)
    WEIGHTS = {
        "task_completion": 0.30,
        "token_efficiency": 0.20,
        "cost_efficiency": 0.20,
        "speed": 0.15,
        "reliability": 0.15,
    }

    def __init__(self, db_session):
        self.db = db_session

    def evaluate_agent(
        self,
        business_id: UUID,
        role_name: str,
        days: int = 30,
    ) -> Dict:
        """Evaluate an agent's performance over a time period.

        Returns a score from 0-100 and improvement suggestions.
        """
        from app.models.agent_execution import AgentExecution
        from sqlalchemy import select

        cutoff = datetime.utcnow() - timedelta(days=days)

        query = (
            select(AgentExecution)
            .where(AgentExecution.business_id == business_id)
            .where(AgentExecution.role_name == role_name)
            .where(AgentExecution.created_at >= cutoff)
        )
        result = self.db.execute(query)
        executions = result.scalars().all()

        if not executions:
            return {
                "role_name": role_name,
                "score": None,
                "total_executions": 0,
                "message": "No execution data available for evaluation",
            }

        total = len(executions)
        success_rate = sum(1 for e in executions if e.success) / total

        # Calculate sub-scores
        task_completion_score = success_rate * 100

        avg_input_tokens = sum(e.input_tokens or 0 for e in executions) / total if total else 0
        avg_output_tokens = sum(e.output_tokens or 0 for e in executions) / total if total else 0
        total_tokens = avg_input_tokens + avg_output_tokens
        # Ideal: under 2000 tokens for a task
        token_efficiency_score = max(0, min(100, (1 - total_tokens / 5000) * 100))

        avg_cost = sum(e.cost_usd or 0 for e in executions) / total
        # Ideal: under $0.01 per execution
        cost_efficiency_score = max(0, min(100, (1 - avg_cost / 0.05) * 100))

        avg_duration = sum(e.duration_ms or 0 for e in executions) / total
        # Ideal: under 2 seconds
        speed_score = max(0, min(100, (1 - avg_duration / 5000) * 100))

        success_score = (
            task_completion_score * self.WEIGHTS["task_completion"]
            + token_efficiency_score * self.WEIGHTS["token_efficiency"]
            + cost_efficiency_score * self.WEIGHTS["cost_efficiency"]
            + speed_score * self.WEIGHTS["speed"]
            + success_rate * 100 * self.WEIGHTS["reliability"]
        )

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            task_completion_score,
            token_efficiency_score,
            cost_efficiency_score,
            speed_score,
            success_rate,
        )

        # Trend analysis: compare with previous period
        previous_cutoff = cutoff - timedelta(days=days)
        previous_query = (
            select(AgentExecution)
            .where(AgentExecution.business_id == business_id)
            .where(AgentExecution.role_name == role_name)
            .where(AgentExecution.created_at >= previous_cutoff)
            .where(AgentExecution.created_at < cutoff)
        )
        previous_result = self.db.execute(previous_query)
        previous_executions = previous_result.scalars().all()

        trend = "stable"
        if previous_executions:
            prev_success = sum(1 for e in previous_executions if e.success) / len(
                previous_executions
            )
            if success_rate > prev_success + 0.05:
                trend = "improving"
            elif success_rate < prev_success - 0.05:
                trend = "declining"

        return {
            "role_name": role_name,
            "score": round(success_score, 1),
            "grade": self._grade(score=success_score),
            "total_executions": total,
            "success_rate": round(success_rate, 4),
            "avg_cost_usd": round(avg_cost, 6),
            "avg_duration_ms": round(avg_duration, 1),
            "avg_tokens": round(total_tokens, 1),
            "sub_scores": {
                "task_completion": round(task_completion_score, 1),
                "token_efficiency": round(token_efficiency_score, 1),
                "cost_efficiency": round(cost_efficiency_score, 1),
                "speed": round(speed_score, 1),
            },
            "trend": trend,
            "suggestions": suggestions,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    def evaluate_business(self, business_id: UUID, days: int = 30) -> Dict:
        """Evaluate all agents for a business."""
        from app.models.agent_execution import AgentExecution
        from sqlalchemy import select

        query = (
            select(AgentExecution.role_name)
            .where(AgentExecution.business_id == business_id)
            .distinct()
        )
        result = self.db.execute(query)
        roles = [row[0] for row in result.fetchall()]

        evaluations = []
        for role in roles:
            evaluations.append(self.evaluate_agent(business_id, role, days))

        avg_score = (
            round(
                sum(e["score"] for e in evaluations if e["score"] is not None)
                / max(len(evaluations), 1),
                1,
            )
            if evaluations
            else None
        )

        return {
            "business_id": str(business_id),
            "overall_score": avg_score,
            "evaluations": evaluations,
            "summary": {
                "total_agents": len(evaluations),
                "top_performer": (
                    max(evaluations, key=lambda x: x["score"] or 0)["role_name"]
                    if evaluations
                    else None
                ),
                "needs_improvement": [
                    e["role_name"]
                    for e in evaluations
                    if e["score"] is not None and e["score"] < 60
                ],
            },
        }

    def _generate_suggestions(
        self,
        task_completion: float,
        token_efficiency: float,
        cost_efficiency: float,
        speed: float,
        success_rate: float,
    ) -> List[Dict]:
        suggestions = []

        if task_completion < 80:
            suggestions.append(
                {
                    "area": "task_completion",
                    "priority": "high",
                    "suggestion": "Review failed tasks and refine tool usage instructions",
                    "impact": "Improved reliability",
                }
            )

        if token_efficiency < 60:
            suggestions.append(
                {
                    "area": "token_efficiency",
                    "priority": "medium",
                    "suggestion": "Optimize prompts to reduce token usage",
                    "impact": "Lower costs and faster execution",
                }
            )

        if cost_efficiency < 50:
            suggestions.append(
                {
                    "area": "cost_efficiency",
                    "priority": "high",
                    "suggestion": "Consider cheaper models or caching strategies",
                    "impact": "Significant cost reduction",
                }
            )

        if speed < 60:
            suggestions.append(
                {
                    "area": "speed",
                    "priority": "medium",
                    "suggestion": "Parallelize independent operations",
                    "impact": "Faster task completion",
                }
            )

        if success_rate < 0.9:
            suggestions.append(
                {
                    "area": "reliability",
                    "priority": "high",
                    "suggestion": "Add retry logic and fallback strategies",
                    "impact": "Higher success rate",
                }
            )

        if not suggestions:
            suggestions.append(
                {
                    "area": "overall",
                    "priority": "info",
                    "suggestion": "Performance is excellent across all metrics",
                    "impact": "Continue current strategy",
                }
            )

        return suggestions

    def _grade(self, score: float) -> str:
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
