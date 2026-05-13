from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import logging
from app.agents.base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

CONTENT_PROMPT = """You are a marketing content creator. Generate marketing content for a business.

Return JSON with:
- content: the main content text
- subject: content subject/headline
- seo_keywords: array of target keywords
- seo_score: 0-100 SEO optimization score
- estimated_read_time_minutes: integer
- hashtags: array of recommended hashtags
- platform_suggestions: array of {platform, recommended_format, best_time_to_post}

Business: {business_name}
Description: {description}
Content type: {content_type}
Target audience: {target_audience}
Tone: {tone}

Return ONLY valid JSON."""


class MarketerAgent(BaseAgent):
    """AI Marketer agent that generates marketing content using LLM"""

    def __init__(self, business_id: UUID, config: Dict[str, Any]):
        super().__init__(business_id, "marketer", config)

    def get_tools(self) -> List:
        return []

    async def execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> AgentResult:
        if task_type == "create_social_post":
            return await self._create_social_post(input_data)
        elif task_type == "write_blog_post":
            return await self._write_blog_post(input_data)
        elif task_type == "create_email_campaign":
            return await self._create_email_campaign(input_data)
        elif task_type == "create_launch_strategy":
            return await self._create_launch_strategy(input_data)
        elif task_type == "execute_scheduled_content":
            return await self._execute_scheduled_content(input_data)
        elif task_type == "analyze_performance":
            return await self._analyze_performance(input_data)
        elif task_type == "generate_hashtags":
            return await self._generate_hashtags(input_data)
        else:
            return AgentResult(
                success=False,
                output=None,
                error=f"Unknown task type: {task_type}"
            )

    async def _create_social_post(self, data: Dict[str, Any]) -> AgentResult:
        platform = data.get("platform", "twitter")
        prompt = CONTENT_PROMPT.format(
            business_name=data.get("business_name", "Business"),
            description=data.get("description", ""),
            content_type=f"social media post for {platform}",
            target_audience=data.get("target_audience", "general"),
            tone=data.get("tone", "professional"),
        )
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a social media marketer.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False,
                               tokens_used=getattr(self.llm, "last_token_usage", {}))
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _write_blog_post(self, data: Dict[str, Any]) -> AgentResult:
        prompt = CONTENT_PROMPT.format(
            business_name=data.get("business_name", "Business"),
            description=data.get("description", ""),
            content_type=f"blog post about {data.get('topic', data.get('description', ''))}",
            target_audience=data.get("target_audience", "general"),
            tone=data.get("tone", "informative"),
        )
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a content writer.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False,
                               tokens_used=getattr(self.llm, "last_token_usage", {}))
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _create_email_campaign(self, data: Dict[str, Any]) -> AgentResult:
        prompt = f"""Design an email marketing campaign for:

Business: {data.get('business_name')}
Goal: {data.get('goal', 'awareness')}
Audience: {data.get('target_audience', 'general')}

Return JSON with:
- subject_line: email subject
- preview_text: email preview
- body_html: HTML email body
- cta_button: call to action button text
- cta_link: suggested link
- estimated_open_rate: float 0-1
- estimated_click_rate: float 0-1
- send_timing: suggested send time"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are an email marketing specialist.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=True,
                               approval_proposal={"title": f"Send campaign: {output.get('subject_line', '')}"},
                               tokens_used=getattr(self.llm, "last_token_usage", {}))
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _create_launch_strategy(self, data: Dict[str, Any]) -> AgentResult:
        prompt = f"""Create a go-to-market launch strategy for:

Business: {data.get('business_description', data.get('business_name', 'Business'))}
Target audience: {data.get('target_audience', 'general')}
USP: {data.get('unique_selling_points', data.get('usp', []))}
Timeline: {data.get('launch_timeline', '2 weeks')}

Return JSON with:
- launch_phases: array of {{phase, duration_days, activities[], metrics[]}}
- channels: array of {{channel, budget_percent, expected_reach}}
- budget_allocation: {{total_budget, breakdown: {{item, amount}}}}
- kpis: array of key performance indicators
- risk_factors: array of potential risks"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a go-to-market strategist.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=True,
                               approval_proposal={"title": "Approve launch strategy", "description": f"Budget: ${output.get('budget_allocation', {}).get('total_budget', 0):,.0f}"},
                               tokens_used=getattr(self.llm, "last_token_usage", {}))
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _execute_scheduled_content(self, data: Dict[str, Any]) -> AgentResult:
        return AgentResult(success=True, output={"posts_made": 0, "message": "Content scheduling active"}, requires_approval=False)

    async def _analyze_performance(self, data: Dict[str, Any]) -> AgentResult:
        prompt = f"""Analyze marketing performance for:
Period: {data.get('period', 'weekly')}
Channel: {data.get('channel', 'all')}

Return JSON with:
- impressions: integer
- engagement_rate: float
- conversions: integer
- top_performing_content: array of content descriptions
- recommendations: array of improvement suggestions"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a marketing analytics analyst.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _generate_hashtags(self, data: Dict[str, Any]) -> AgentResult:
        prompt = f"""Generate relevant hashtags for:
Topic: {data.get('content', data.get('topic', ''))}
Industry: {data.get('industry', 'technology')}
Count: 10

Return JSON with:
- hashtags: array of hashtag strings
- categories: {{high_reach: [], niche: [], branded: []}}"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a social media hashtag strategist.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))
