import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)

BRAND_PROMPT = """You are a creative brand designer. Create a brand identity for a business.

Return JSON with:
- brand_name: business name
- brand_personality: brand personality description
- color_palette: array of hex colors
- typography: font recommendations
- logo_description: detailed description for a logo
- brand_guidelines: brand usage guidelines
- visual_style: visual style keywords

Business name: {business_name}
Description: {description}
Target audience: {target_audience}
Brand personality: {brand_personality}

Return ONLY valid JSON."""


class DesignerAgent(BaseAgent):
    """AI Designer agent that creates brand identity and design concepts using LLM"""

    def __init__(self, business_id: UUID, config: Dict[str, Any]):
        super().__init__(business_id, "designer", config)

    def get_tools(self) -> List:
        return []

    async def execute_task(
        self, task_type: str, input_data: Dict[str, Any], context: Optional[Dict] = None
    ) -> AgentResult:
        if task_type == "create_brand_identity":
            return await self._create_brand_identity(input_data)
        elif task_type == "create_logo":
            return await self._create_logo(input_data)
        elif task_type == "design_banner":
            return await self._design_banner(input_data)
        elif task_type == "edit_image":
            return await self._edit_image(input_data)
        else:
            return AgentResult(success=False, output=None, error=f"Unknown task type: {task_type}")

    async def _create_brand_identity(self, data: Dict[str, Any]) -> AgentResult:
        business_name = data.get("business_name", "Unknown")
        logger.info(f"Creating brand identity for: {business_name}")

        prompt = BRAND_PROMPT.format(
            business_name=business_name,
            description=data.get("description", ""),
            target_audience=json.dumps(data.get("target_audience", [])),
            brand_personality=data.get("brand_personality", "professional"),
        )

        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a senior brand designer."
            )
            output = json.loads(response)

            return AgentResult(
                success=True,
                output=output,
                requires_approval=True,
                approval_proposal={
                    "title": f"Approve brand identity for {business_name}",
                    "description": f"Color palette: {', '.join(output.get('color_palette', [])[:3])}",
                },
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            logger.error(f"Brand identity failed: {e}")
            return AgentResult(success=False, output=None, error=str(e))

    async def _create_logo(self, data: Dict[str, Any]) -> AgentResult:
        prompt = f"""Design a logo concept for:
Brand: {data.get('business_name', 'Unknown')}
Style: {data.get('style', 'modern')}
Description: {data.get('description', '')}

Return JSON with:
- concept: logo concept description
- colors: recommended colors array
- typography: font recommendation
- variations: array of format variations"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a logo designer.")
            output = json.loads(response)
            return AgentResult(
                success=True,
                output=output,
                requires_approval=False,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _design_banner(self, data: Dict[str, Any]) -> AgentResult:
        prompt = f"""Design a banner/ad concept for:
Brand: {data.get('business_name', 'Unknown')}
Purpose: {data.get('purpose', 'marketing')}
Dimensions: {data.get('dimensions', '1200x628')}

Return JSON with:
- concept: banner concept
- headline: suggested headline text
- cta: call to action text
- color_scheme: color recommendations"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a graphic designer.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _edit_image(self, data: Dict[str, Any]) -> AgentResult:
        prompt = f"""Describe the image editing needed:
Current: {data.get('current_description', '')}
Desired: {data.get('desired_changes', '')}

Return JSON with:
- steps: array of editing steps
- tools_needed: array of tools/techniques
- expected_result: description of final result"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a photo editor.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))
