import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.schemas.researcher_output import Competitor, ResearcherOutput

logger = logging.getLogger(__name__)

MARKET_ANALYSIS_PROMPT = """You are a market research analyst. Analyze this business idea and provide a structured JSON output with:
- business_name: a catchy name for this business
- market_size_usd: total addressable market in USD (float)
- competitors: array of {name, market_share, strengths[], weaknesses[], pricing}
- opportunity_score: 0-100 score
- recommended_positioning: strategy recommendation
- target_audience: array of target customer segments
- tech_stack: array of recommended technologies
- estimated_cac: customer acquisition cost estimate
- estimated_ltv: lifetime value estimate
- business_model: "saas", "subscription", "marketplace", etc.
- brand_personality: brand tone
- usp: unique selling points
- description: business description
- risk_factors: array of potential risks

Business idea: {idea}

Return ONLY valid JSON, no markdown."""


class ResearcherAgent(BaseAgent):
    """AI Researcher agent that conducts market and competitor research using LLM"""

    def __init__(self, business_id: UUID, config: Dict[str, Any]):
        super().__init__(business_id, "researcher", config)

    def get_tools(self) -> List:
        return []

    async def execute_task(
        self, task_type: str, input_data: Dict[str, Any], context: Optional[Dict] = None
    ) -> AgentResult:
        if task_type == "validate_business_idea":
            return await self._validate_business_idea(input_data)
        elif task_type == "market_analysis":
            return await self._conduct_market_analysis(input_data)
        elif task_type == "competitor_research":
            return await self._research_competitors(input_data)
        elif task_type == "trend_analysis":
            return await self._analyze_trends(input_data)
        else:
            return AgentResult(success=False, output=None, error=f"Unknown task type: {task_type}")

    async def _validate_business_idea(self, data: Dict[str, Any]) -> AgentResult:
        idea = data.get("idea", "")
        logger.info(f"Validating business idea: {idea}")

        prompt = MARKET_ANALYSIS_PROMPT.format(idea=idea)
        system = "You are a seasoned startup advisor and market analyst."

        try:
            response = await self.llm.ainvoke(prompt, system_prompt=system)
            output = json.loads(response)
            validated = ResearcherOutput(**output)
            tokens = getattr(self.llm, "last_token_usage", {})

            return AgentResult(
                success=True,
                output=validated.model_dump(),
                requires_approval=validated.opportunity_score < 40,
                approval_proposal=(
                    {
                        "title": f"Low opportunity score: {validated.opportunity_score}/100",
                        "description": f"Business idea '{validated.business_name}' scored low on opportunity. Consider pivoting.",
                        "impact": f"Market size: ${validated.market_size_usd:,.0f}",
                    }
                    if validated.opportunity_score < 40
                    else None
                ),
                tokens_used=tokens,
            )
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return AgentResult(success=False, output=None, error=str(e))

    async def _conduct_market_analysis(self, data: Dict[str, Any]) -> AgentResult:
        return await self._validate_business_idea(data)

    async def _research_competitors(self, data: Dict[str, Any]) -> AgentResult:
        industry = data.get("industry", data.get("idea", "unknown"))
        prompt = f"""Research the competitive landscape for: {industry}

Return JSON with:
- competitors: array of {{name, market_share (float), strengths[], weaknesses[], pricing}}
- market_gaps: array of unmet customer needs
- recommended_positioning: recommended market position"""

        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a competitive intelligence analyst."
            )
            output = json.loads(response)
            competitors = [Competitor(**c) for c in output.get("competitors", [])]

            return AgentResult(
                success=True,
                output={
                    "competitors": [c.model_dump() for c in competitors],
                    "market_gaps": output.get("market_gaps", []),
                    "recommended_positioning": output.get("recommended_positioning", ""),
                },
                requires_approval=False,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            logger.error(f"Competitor research failed: {e}")
            return AgentResult(success=False, output=None, error=str(e))

    async def _analyze_trends(self, data: Dict[str, Any]) -> AgentResult:
        sector = data.get("sector", data.get("idea", "technology"))
        prompt = f"""Analyze current market trends for: {sector}

Return JSON with:
- emerging_trends: array of {{trend, impact ("High"/"Medium"/"Low"), timeline}}
- declining_trends: array of {{trend, impact, timeline}}"""

        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a market intelligence analyst."
            )
            output = json.loads(response)
            return AgentResult(
                success=True,
                output=output,
                requires_approval=False,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return AgentResult(success=False, output=None, error=str(e))
