from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import logging
from app.agents.base_agent import BaseAgent, AgentResult
from app.agents.schemas.developer_output import DeveloperOutput

logger = logging.getLogger(__name__)

DEV_SPEC_PROMPT = """You are a senior software architect. Given a business idea and specification, design a technical implementation plan.

Return JSON with:
- tech_stack: array of recommended technologies/frameworks
- architecture_summary: high-level architecture description
- features: array of {name, description, priority}
- timeline_weeks: estimated weeks to build (integer)
- estimated_cost_usd: estimated development cost
- version: "1.0.0"
- decisions: array of {category, choice, rationale} for key technical decisions
- risks: array of potential risks

Business name: {business_name}
Description: {description}
Features: {features}
Tech stack context: {tech_stack}

Return ONLY valid JSON."""


class DeveloperAgent(BaseAgent):
    """AI Developer agent that designs and plans application architecture using LLM"""

    def __init__(self, business_id: UUID, config: Dict[str, Any]):
        super().__init__(business_id, "developer", config)

    def get_tools(self) -> List:
        return []

    async def execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> AgentResult:
        if task_type == "generate_application":
            return await self._generate_full_application(input_data)
        elif task_type == "fix_bug":
            return await self._handle_bug_fix(input_data)
        elif task_type == "implement_feature":
            return await self._implement_feature(input_data)
        elif task_type == "deploy":
            return await self._handle_deployment(input_data)
        else:
            return AgentResult(
                success=False,
                output=None,
                error=f"Unknown task type: {task_type}"
            )

    async def _generate_full_application(self, spec: Dict[str, Any]) -> AgentResult:
        business_name = spec.get("business_name", "Unknown")
        logger.info(f"Generating application architecture for: {business_name}")

        prompt = DEV_SPEC_PROMPT.format(
            business_name=business_name,
            description=spec.get("description", ""),
            features=json.dumps(spec.get("features", [])),
            tech_stack=json.dumps(spec.get("tech_stack", [])),
        )

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a senior software architect.")
            output = json.loads(response)
            validated = DeveloperOutput(**output)

            requires_approval = validated.estimated_cost_usd > 10000

            return AgentResult(
                success=True,
                output=validated.model_dump(),
                requires_approval=requires_approval,
                approval_proposal={
                    "title": f"Approve architecture for {business_name}",
                    "description": f"Estimated {validated.timeline_weeks} weeks, ${validated.estimated_cost_usd:,.0f}",
                    "impact": f"Tech stack: {', '.join(validated.tech_stack[:3])}",
                } if requires_approval else None,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            logger.error(f"Application generation failed: {e}")
            return AgentResult(success=False, output=None, error=str(e))

    async def _handle_bug_fix(self, bug_data: Dict[str, Any]) -> AgentResult:
        description = bug_data.get("description", "")
        severity = bug_data.get("severity", "medium")
        logger.info(f"Analyzing bug: {description}")

        prompt = f"""Analyze this bug report and provide a fix plan:

Description: {description}
Severity: {severity}

Return JSON with:
- root_cause: root cause analysis
- fix_summary: summary of the fix
- estimated_minutes: estimated fix time
- requires_deploy: boolean
- tests_to_run: array of test suggestions"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a senior software engineer debugging an issue.")
            output = json.loads(response)
            auto_deploy = severity == "critical"

            return AgentResult(
                success=True,
                output={**output, "fix_ready": True},
                requires_approval=not auto_deploy,
                approval_proposal={
                    "title": f"Deploy bug fix: {description[:50]}",
                    "description": output.get("fix_summary", ""),
                } if not auto_deploy else None,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            logger.error(f"Bug fix failed: {e}")
            return AgentResult(success=False, output=None, error=str(e))

    async def _implement_feature(self, feature_data: Dict[str, Any]) -> AgentResult:
        name = feature_data.get("name", "Unknown feature")
        spec = feature_data.get("specification", {})
        logger.info(f"Planning feature: {name}")

        prompt = f"""Design implementation plan for this feature:

Name: {name}
Specification: {json.dumps(spec)}

Return JSON with:
- implementation_summary: how to implement this
- estimated_hours: integer
- changes_database: boolean
- breaking_changes: boolean
- files_to_modify: array of file paths
- test_strategy: testing approach"""

        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a software engineer planning a feature implementation.")
            output = json.loads(response)

            requires_approval = output.get("changes_database", False) or output.get("breaking_changes", False) or output.get("estimated_hours", 0) > 8

            return AgentResult(
                success=True,
                output=output,
                requires_approval=requires_approval,
                approval_proposal={
                    "title": f"Feature: {name}",
                    "description": output.get("implementation_summary", ""),
                    "estimated_hours": output.get("estimated_hours", 0),
                    "breaking_changes": output.get("breaking_changes", False),
                } if requires_approval else None,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            logger.error(f"Feature planning failed: {e}")
            return AgentResult(success=False, output=None, error=str(e))

    async def _handle_deployment(self, deploy_data: Dict[str, Any]) -> AgentResult:
        environment = deploy_data.get("environment", "production")
        version = deploy_data.get("version", "1.0.0")
        changelog = deploy_data.get("changelog", "")

        if environment == "production":
            return AgentResult(
                success=True,
                output={"ready_for_deployment": True, "version": version},
                requires_approval=True,
                approval_proposal={
                    "title": f"Deploy to Production: {version}",
                    "description": changelog or "Standard production deployment",
                }
            )

        return AgentResult(
            success=True,
            output={"deployment_url": f"staging-{version}", "environment": environment},
            requires_approval=False,
        )
