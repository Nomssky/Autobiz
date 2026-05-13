from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import logging
import asyncio
from datetime import datetime
from app.agents.base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class SupportAgent(BaseAgent):
    """AI Support agent that handles customer tickets and provides 24/7 support"""

    def __init__(self, business_id: UUID, config: Dict[str, Any]):
        super().__init__(business_id, "support", config)
        # In a real implementation, these would be initialized properly
        self.ticket_system = None  # Ticket system client
        self.knowledge_base = None  # Knowledge base for auto-responses

    def get_tools(self) -> List:
        """Return list of tools available to this agent"""
        return [
            {
                "name": "process_ticket",
                "description": "Process and respond to a customer support ticket",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string"},
                        "customer_id": {"type": "string"},
                        "subject": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "category": {"type": "string", "enum": ["bug", "billing", "feature_request", "how_to", "account", "performance", "security"]}
                    },
                    "required": ["ticket_id", "customer_id", "subject", "description"]
                }
            },
            {
                "name": "auto_respond",
                "description": "Generate an auto-response for common support inquiries",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string"},
                        "category": {"type": "string", "enum": ["password_reset", "billing_inquiry", "feature_question", "bug_report", "general"]},
                        "language": {"type": "string", "default": "en"}
                    },
                    "required": ["ticket_id", "category"]
                }
            },
            {
                "name": "escalate_ticket",
                "description": "Escalate a ticket to a human agent or specialized team",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string"},
                        "reason": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "target_team": {"type": "string", "enum": ["engineering", "billing", "security", "product", "management"]}
                    },
                    "required": ["ticket_id", "reason", "target_team"]
                }
            },
            {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base for relevant articles",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "category": {"type": "string"},
                        "limit": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "analyze_sentiment",
                "description": "Analyze customer sentiment from ticket content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "string"},
                        "text": {"type": "string"}
                    },
                    "required": ["ticket_id", "text"]
                }
            },
            {
                "name": "generate_support_report",
                "description": "Generate a support metrics and analytics report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "enum": ["daily", "weekly", "monthly"], "default": "weekly"},
                        "metrics": {"type": "array", "items": {"type": "string"}},
                        "format": {"type": "string", "enum": ["summary", "detailed", "csv"], "default": "summary"}
                    },
                    "required": ["period"]
                }
            }
        ]

    async def execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> AgentResult:
        """Execute support task based on type"""

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
            return AgentResult(
                success=False,
                output=None,
                error=f"Unknown task type: {task_type}"
            )

    async def _process_ticket(self, params: Dict[str, Any]) -> AgentResult:
        """Process and respond to a customer support ticket"""
        ticket_id = params.get("ticket_id", "")
        customer_id = params.get("customer_id", "")
        subject = params.get("subject", "")
        description = params.get("description", "")
        priority = params.get("priority", "medium")
        category = params.get("category", "general")

        logger.info(f"Processing ticket {ticket_id} from customer {customer_id}")

        try:
            await asyncio.sleep(1)

            # Analyze sentiment of the ticket
            sentiment = self._mock_sentiment_analysis(description)

            # Search knowledge base for relevant solutions
            kb_results = self._mock_kb_search(subject, category)

            output = {
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "subject": subject,
                "category": category,
                "priority": priority,
                "sentiment": sentiment,
                "knowledge_base_results": kb_results,
                "suggested_response": self._generate_response(category, subject, kb_results),
                "requires_escalation": priority in ("high", "critical") and category in ("security", "bug"),
                "estimated_resolution_time": self._estimate_resolution_time(category, priority),
                "status": "in_progress"
            }

            # Critical security issues always require escalation
            requires_approval = category == "security" or (priority == "critical" and category == "bug")

            approval_proposal = None
            if requires_approval:
                approval_proposal = {
                    "title": f"Escalate {category} ticket #{ticket_id}",
                    "description": f"Ticket requires escalation: {subject}",
                    "priority": priority,
                    "category": category,
                    "customer_id": customer_id,
                    "reason": "Critical security or bug issue requiring specialized team"
                }

            return AgentResult(
                success=True,
                output=output,
                requires_approval=requires_approval,
                approval_proposal=approval_proposal
            )

        except Exception as e:
            logger.error(f"Ticket processing failed: {str(e)}")
            return AgentResult(
                success=False,
                output=None,
                error=f"Ticket processing failed: {str(e)}"
            )

    async def _auto_respond(self, params: Dict[str, Any]) -> AgentResult:
        """Generate an auto-response for common support inquiries"""
        ticket_id = params.get("ticket_id", "")
        category = params.get("category", "general")
        language = params.get("language", "en")

        logger.info(f"Generating auto-response for ticket {ticket_id} in {language}")

        try:
            await asyncio.sleep(0.5)

            auto_responses = {
                "password_reset": {
                    "response": "Hello, to reset your password please click here: [reset link]. If you did not request this, please ignore this email.",
                    "subject": "Password Reset Instructions",
                    "template": "password_reset_default"
                },
                "billing_inquiry": {
                    "response": "Thank you for your billing inquiry. Your current plan details and recent charges can be viewed at [billing page]. For specific questions, our billing team typically responds within 24 hours.",
                    "subject": "Re: Billing Inquiry",
                    "template": "billing_inquiry_default"
                },
                "feature_question": {
                    "response": "Thank you for your question! Our documentation at [docs link] covers this feature in detail. If you need further assistance, please do not hesitate to ask.",
                    "subject": "Re: Feature Question",
                    "template": "feature_question_default"
                },
                "bug_report": {
                    "response": "We have received your bug report and our engineering team is investigating. We will update you within 4 hours with a status. Reference: #{ticket_id}",
                    "subject": "Re: Bug Report Acknowledged",
                    "template": "bug_report_default"
                },
                "general": {
                    "response": "Thank you for contacting support. A team member will review your inquiry and respond within 24 hours.",
                    "subject": "Re: Support Request",
                    "template": "general_default"
                }
            }

            response_data = auto_responses.get(category, auto_responses["general"])
            response_data["ticket_id"] = ticket_id
            response_data["language"] = language
            response_data["auto_generated"] = True
            response_data["generated_at"] = datetime.utcnow().isoformat()

            return AgentResult(
                success=True,
                output=response_data,
                requires_approval=False
            )

        except Exception as e:
            logger.error(f"Auto-response generation failed: {str(e)}")
            return AgentResult(
                success=False,
                output=None,
                error=f"Auto-response generation failed: {str(e)}"
            )

    async def _escalate_ticket(self, params: Dict[str, Any]) -> AgentResult:
        """Escalate a ticket to a human agent or specialized team"""
        ticket_id = params.get("ticket_id", "")
        reason = params.get("reason", "")
        priority = params.get("priority", "medium")
        target_team = params.get("target_team", "engineering")

        logger.info(f"Escalating ticket {ticket_id} to {target_team} team")

        try:
            await asyncio.sleep(0.5)

            escalation_id = f"esc_{hash(ticket_id + target_team) % 10000000:07d}"

            output = {
                "escalation_id": escalation_id,
                "ticket_id": ticket_id,
                "target_team": target_team,
                "priority": priority,
                "reason": reason,
                "status": "escalated",
                "created_at": datetime.utcnow().isoformat(),
                "sla_response_minutes": {
                    "critical": 15,
                    "high": 60,
                    "medium": 240,
                    "low": 1440
                }.get(priority, 240),
                "assigned_to": f"{target_team}-team"
            }

            return AgentResult(
                success=True,
                output=output,
                requires_approval=priority in ("high", "critical")
            )

        except Exception as e:
            logger.error(f"Ticket escalation failed: {str(e)}")
            return AgentResult(
                success=False,
                output=None,
                error=f"Ticket escalation failed: {str(e)}"
            )

    async def _search_knowledge_base(self, params: Dict[str, Any]) -> AgentResult:
        """Search the knowledge base for relevant articles"""
        query = params.get("query", "")
        category = params.get("category", "")
        limit = params.get("limit", 5)

        logger.info(f"Searching knowledge base for: {query}")

        try:
            await asyncio.sleep(0.5)

            # Mock KB articles
            all_articles = [
                {"id": "kb_001", "title": "How to Reset Your Password", "category": "account", "relevance": 0.95, "summary": "Steps to reset your password via email."},
                {"id": "kb_002", "title": "Understanding Billing Cycles", "category": "billing", "relevance": 0.90, "summary": "Explanation of monthly vs annual billing."},
                {"id": "kb_003", "title": "Getting Started Guide", "category": "how_to", "relevance": 0.88, "summary": "Quick start tutorial for new users."},
                {"id": "kb_004", "title": "API Rate Limits", "category": "performance", "relevance": 0.85, "summary": "Current API rate limits and how to optimize."},
                {"id": "kb_005", "title": "Two-Factor Authentication Setup", "category": "security", "relevance": 0.92, "summary": "How to enable 2FA on your account."},
                {"id": "kb_006", "title": "Common Error Codes", "category": "bug", "relevance": 0.80, "summary": "List of common error codes and solutions."},
                {"id": "kb_007", "title": "Feature: Bulk Export", "category": "feature", "relevance": 0.70, "summary": "How to use the bulk export feature."},
                {"id": "kb_008", "title": "Data Privacy & GDPR", "category": "security", "relevance": 0.75, "summary": "Our data privacy practices and GDPR compliance."},
            ]

            # Filter by category if specified
            if category:
                filtered = [a for a in all_articles if a["category"] == category]
            else:
                filtered = all_articles

            # Sort by relevance and take top N
            filtered.sort(key=lambda x: x["relevance"], reverse=True)
            results = filtered[:limit]

            return AgentResult(
                success=True,
                output={
                    "query": query,
                    "category_filter": category,
                    "results": results,
                    "total_matches": len(results),
                    "search_time_ms": 45
                },
                requires_approval=False
            )

        except Exception as e:
            logger.error(f"Knowledge base search failed: {str(e)}")
            return AgentResult(
                success=False,
                output=None,
                error=f"Knowledge base search failed: {str(e)}"
            )

    async def _analyze_sentiment(self, params: Dict[str, Any]) -> AgentResult:
        """Analyze customer sentiment from ticket content"""
        ticket_id = params.get("ticket_id", "")
        text = params.get("text", "")

        logger.info(f"Analyzing sentiment for ticket {ticket_id}")

        try:
            await asyncio.sleep(0.5)

            # Mock sentiment analysis
            negative_keywords = ["angry", "frustrated", "terrible", "awful", "hate", "worst", "broken", "unacceptable"]
            positive_keywords = ["great", "love", "amazing", "helpful", "thank", "excellent", "perfect"]

            text_lower = text.lower()
            neg_count = sum(1 for word in negative_keywords if word in text_lower)
            pos_count = sum(1 for word in positive_keywords if word in text_lower)

            if neg_count > pos_count:
                sentiment = "negative"
                score = -0.5 - (neg_count * 0.1)
            elif pos_count > neg_count:
                sentiment = "positive"
                score = 0.5 + (pos_count * 0.1)
            else:
                sentiment = "neutral"
                score = 0.0

            score = max(-1.0, min(1.0, score))

            output = {
                "ticket_id": ticket_id,
                "sentiment": sentiment,
                "score": round(score, 2),
                "confidence": round(0.75 + abs(score) * 0.2, 2),
                "keywords_found": {
                    "negative": [w for w in negative_keywords if w in text_lower],
                    "positive": [w for w in positive_keywords if w in text_lower]
                },
                "recommendation": "Prioritize response" if sentiment == "negative" else "Standard priority"
            }

            return AgentResult(
                success=True,
                output=output,
                requires_approval=False
            )

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return AgentResult(
                success=False,
                output=None,
                error=f"Sentiment analysis failed: {str(e)}"
            )

    async def _generate_support_report(self, params: Dict[str, Any]) -> AgentResult:
        """Generate a support metrics and analytics report"""
        period = params.get("period", "weekly")
        metrics = params.get("metrics", ["ticket_volume", "resolution_time", "customer_satisfaction", "first_response_time"])
        format_type = params.get("format", "summary")

        logger.info(f"Generating support report for {period} period")

        try:
            await asyncio.sleep(1.5)

            output = {
                "period": period,
                "metrics": {
                    "ticket_volume": {
                        "total_tickets": 847,
                        "new_tickets": 124,
                        "resolved_tickets": 118,
                        "open_tickets": 53,
                        "trend": "increasing"
                    },
                    "resolution_time": {
                        "avg_resolution_hours": 4.2,
                        "median_resolution_hours": 3.1,
                        "p95_resolution_hours": 24.0,
                        "sla_compliance_rate": 0.92
                    },
                    "customer_satisfaction": {
                        "csat_score": 4.3,
                        "response_rate": 0.89,
                        "nps_score": 42
                    },
                    "first_response_time": {
                        "avg_minutes": 12,
                        "p95_minutes": 45,
                        "target_minutes": 15
                    }
                },
                "top_categories": [
                    {"category": "billing", "count": 210, "percentage": 24.8},
                    {"category": "how_to", "count": 185, "percentage": 21.8},
                    {"category": "bug", "count": 156, "percentage": 18.4},
                    {"category": "feature_request", "count": 134, "percentage": 15.8}
                ],
                "agent_performance": {
                    "auto_resolved_rate": 0.67,
                    "escalation_rate": 0.12,
                    "avg_touches_per_ticket": 1.8
                },
                "recommendations": [
                    "Increase knowledge base coverage for billing inquiries to reduce ticket volume",
                    "Consider adding more chatbot flows for password resets (30% of tickets)",
                    "Bug resolution time exceeds SLA - investigate engineering team capacity"
                ]
            }

            # Filter metrics if specific ones requested
            if metrics != ["ticket_volume", "resolution_time", "customer_satisfaction", "first_response_time"]:
                output["metrics"] = {k: v for k, v in output["metrics"].items() if k in metrics}

            return AgentResult(
                success=True,
                output=output,
                requires_approval=False
            )

        except Exception as e:
            logger.error(f"Support report generation failed: {str(e)}")
            return AgentResult(
                success=False,
                output=None,
                error=f"Support report generation failed: {str(e)}"
            )

    async def _process_pending_tickets(self, params: Dict[str, Any]) -> AgentResult:
        """Process batch of pending tickets"""
        batch_size = params.get("batch_size", 20)

        logger.info(f"Processing pending tickets (batch size: {batch_size})")

        try:
            await asyncio.sleep(2)

            # Mock processing
            processed = []
            for i in range(batch_size):
                processed.append({
                    "ticket_id": f"ticket_{1000 + i}",
                    "auto_resolved": i % 3 != 0,  # 67% auto-resolved
                    "category": ["billing", "how_to", "bug", "general"][i % 4],
                    "response_time_seconds": (i % 10 + 1) * 30
                })

            auto_resolved = sum(1 for t in processed if t["auto_resolved"])
            escalated = sum(1 for t in processed if not t["auto_resolved"])

            output = {
                "processed_count": len(processed),
                "auto_resolved": auto_resolved,
                "escalated": escalated,
                "avg_response_time_seconds": sum(t["response_time_seconds"] for t in processed) / len(processed),
                "tickets": processed[:10]  # Return first 10 as sample
            }

            return AgentResult(
                success=True,
                output=output,
                requires_approval=False
            )

        except Exception as e:
            logger.error(f"Pending ticket processing failed: {str(e)}")
            return AgentResult(
                success=False,
                output=None,
                error=f"Pending ticket processing failed: {str(e)}"
            )

    def _mock_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Mock sentiment analysis"""
        text_lower = text.lower()
        negative_words = ["angry", "frustrated", "terrible", "broken", "hate"]
        positive_words = ["great", "thanks", "happy", "love"]

        neg = sum(1 for w in negative_words if w in text_lower)
        pos = sum(1 for w in positive_words if w in text_lower)

        if neg > pos:
            label = "negative"
            score = -0.5
        elif pos > neg:
            label = "positive"
            score = 0.7
        else:
            label = "neutral"
            score = 0.0

        return {"label": label, "score": score, "confidence": 0.8}

    def _mock_kb_search(self, subject: str, category: str) -> List[Dict]:
        """Mock knowledge base search results"""
        articles = [
            {"id": "kb_001", "title": "Getting Started", "relevance": 0.9},
            {"id": "kb_002", "title": "Common Issues", "relevance": 0.8},
            {"id": "kb_003", "title": "FAQ", "relevance": 0.7},
        ]
        return [a for a in articles if a["relevance"] > 0.5][:3]

    def _generate_response(self, category: str, subject: str, kb_results: List[Dict]) -> str:
        """Generate a suggested response based on category and KB results"""
        responses = {
            "password_reset": "Please follow the password reset instructions sent to your email.",
            "billing_inquiry": "Your billing information is available in your account dashboard.",
            "feature_question": "This feature is available in your current plan. Check the documentation for details.",
            "bug_report": "We have logged this bug and our team is investigating.",
        }
        return responses.get(category, f"Thank you for your inquiry regarding: {subject}")

    def _estimate_resolution_time(self, category: str, priority: str) -> str:
        """Estimate resolution time based on category and priority"""
        resolution_map = {
            ("password_reset", "low"): "5 minutes",
            ("password_reset", "medium"): "15 minutes",
            ("billing_inquiry", "low"): "4 hours",
            ("billing_inquiry", "medium"): "8 hours",
            ("bug", "high"): "24 hours",
            ("bug", "critical"): "4 hours",
            ("security", "critical"): "1 hour",
            ("security", "high"): "4 hours",
        }
        return resolution_map.get((category, priority), "24 hours")


# Import asyncio at the top to avoid issues
import asyncio
