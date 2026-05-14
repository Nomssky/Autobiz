import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class SupportAgent(BaseAgent):
    """AI Support agent that handles customer inquiries using LLM"""

    def __init__(self, business_id: UUID, config: Dict[str, Any]):
        super().__init__(business_id, "support", config)

    def get_tools(self) -> List:
        return []

    async def execute_task(
        self, task_type: str, input_data: Dict[str, Any], context: Optional[Dict] = None
    ) -> AgentResult:
        if task_type == "process_ticket":
            return await self._process_ticket(input_data)
        elif task_type == "auto_respond":
            return await self._auto_respond(input_data)
        elif task_type == "escalate_ticket":
            return await self._escalate_ticket(input_data)
        elif task_type == "search_knowledge_base":
            return await self._search_knowledge_base(input_data)
        elif task_type == "analyze_sentiment":
            return await self._analyze_sentiment(input_data)
        elif task_type == "generate_support_report":
            return await self._generate_support_report(input_data)
        elif task_type == "process_pending_tickets":
            return await self._process_pending_tickets(input_data)
        else:
            return AgentResult(success=False, output=None, error=f"Unknown task type: {task_type}")

    async def _process_ticket(self, params: Dict[str, Any]) -> AgentResult:
        ticket_id = params.get("ticket_id", "")
        subject = params.get("subject", "")
        description = params.get("description", "")
        category = params.get("category", "general")

        prompt = f"""Process this support ticket:
Subject: {subject}
Description: {description}
Category: {category}

Return JSON with:
- suggested_response: suggested reply text
- sentiment: positive/negative/neutral
- priority: low/medium/high/critical
- requires_escalation: boolean
- estimated_resolution_minutes: integer
- kb_articles: array of relevant article titles"""

        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a customer support agent."
            )
            output = json.loads(response)
            requires_escalation = output.get("requires_escalation", False) or category == "security"

            return AgentResult(
                success=True,
                output={
                    **output,
                    "ticket_id": ticket_id,
                    "status": "resolved" if not requires_escalation else "escalated",
                },
                requires_approval=requires_escalation,
                approval_proposal=(
                    {
                        "title": f"Escalate ticket #{ticket_id}",
                        "description": subject,
                        "priority": output.get("priority", "medium"),
                    }
                    if requires_escalation
                    else None
                ),
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _auto_respond(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Generate an auto-response for:
Category: {params.get('category', 'general')}
Language: {params.get('language', 'en')}
Ticket: {params.get('ticket_id', '')}

Return JSON with:
- response: auto-response text
- subject: email subject
- template: template name used
- resolved: boolean"""

        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are an automated support responder."
            )
            output = json.loads(response)
            return AgentResult(
                success=True,
                output={**output, "ticket_id": params.get("ticket_id", ""), "auto_generated": True},
                requires_approval=False,
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _escalate_ticket(self, params: Dict[str, Any]) -> AgentResult:
        return AgentResult(
            success=True,
            output={
                "ticket_id": params.get("ticket_id", ""),
                "target_team": params.get("target_team", "engineering"),
                "priority": params.get("priority", "medium"),
                "status": "escalated",
                "created_at": datetime.utcnow().isoformat(),
            },
            requires_approval=False,
        )

    async def _search_knowledge_base(self, params: Dict[str, Any]) -> AgentResult:
        query = params.get("query", "")
        prompt = f"""Search knowledge base for: {query}
Category: {params.get('category', '')}
Limit: {params.get('limit', 5)}

Return JSON with results array of {{title, summary, relevance_score, category}}"""

        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a knowledge base search system."
            )
            output = json.loads(response)
            return AgentResult(
                success=True,
                output={"query": query, "results": output.get("results", [])},
                requires_approval=False,
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _analyze_sentiment(self, params: Dict[str, Any]) -> AgentResult:
        text = params.get("text", "")
        prompt = f"""Analyze customer sentiment from this text:
{text}

Return JSON with:
- sentiment: positive/neutral/negative
- score: float from -1.0 to 1.0
- confidence: float 0-1
- key_phrases: array of key phrases
- urgency: low/medium/high"""

        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a sentiment analysis AI."
            )
            output = json.loads(response)
            return AgentResult(
                success=True,
                output={**output, "ticket_id": params.get("ticket_id", "")},
                requires_approval=False,
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _generate_support_report(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Generate a support metrics report for period: {params.get('period', 'weekly')}

Return JSON with:
- ticket_volume: {{total, new, resolved, open}}
- resolution_time: {{avg_hours, p95_hours, sla_compliance}}
- customer_satisfaction: {{csat_score, response_rate}}
- top_categories: array of {{category, count, percentage}}
- recommendations: array of improvement suggestions"""

        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a support analytics analyst."
            )
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _process_pending_tickets(self, params: Dict[str, Any]) -> AgentResult:
        from app.database import get_db_session
        from app.models.agent_task import AgentTask
        from sqlalchemy import select

        try:
            batch_size = params.get("batch_size", 10)
            with get_db_session() as session:
                result = session.execute(
                    select(AgentTask)
                    .where(AgentTask.business_id == self.business_id)
                    .where(AgentTask.task_type.like("%support%"))
                    .where(AgentTask.status == "pending")
                    .limit(batch_size)
                )
                tickets = result.scalars().all()
                processed = 0
                for ticket in tickets:
                    prompt = f"""Process this support ticket:
Ticket type: {ticket.task_type}
Input: {ticket.input_data}

Generate a response. Return JSON with:
- ticket_id: {ticket.id}
- response_text: your response to the customer
- sentiment: positive/neutral/negative
- priority: low/medium/high
- requires_escalation: boolean
- resolution_time_minutes: integer"""
                    try:
                        resp = await self.llm.ainvoke(
                            prompt, system_prompt="You are a customer support agent."
                        )
                        output = json.loads(resp)
                        ticket.output_data = output
                        ticket.status = "completed"
                        processed += 1
                    except Exception as e:
                        logger.warning(f"Failed to process ticket {ticket.id}: {e}")
                        ticket.status = "failed"
                        ticket.error_message = str(e)
                session.commit()
                return AgentResult(
                    success=True,
                    output={
                        "processed_count": processed,
                        "total_found": len(tickets),
                        "message": f"Processed {processed} of {len(tickets)} pending tickets",
                    },
                    requires_approval=False,
                )
        except Exception as e:
            return AgentResult(success=False, output=None, error=f"Ticket processing error: {e}")
