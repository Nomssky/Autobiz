"""CrewAI agent configurations with tool assignments."""

from typing import Any, Dict
from uuid import UUID

from app.config import settings


def create_agent_configs(business_id: UUID) -> Dict[str, Dict[str, Any]]:
    """Create CrewAI agent configurations with roles and tools."""
    return {
        "researcher": {
            "role": "Market Research Agent",
            "goal": "Provide comprehensive market intelligence",
            "backstory": "Expert market analyst with access to web search and trend analysis tools",
            "allow_delegation": False,
            "verbose": True,
            "tools": ["web_search_tool", "competitor_analysis_tool", "trend_analysis_tool"],
            "max_iterations": 3,
        },
        "business_strategist": {
            "role": "Business Strategy Agent",
            "goal": "Translate research into actionable business plans",
            "backstory": "Seasoned business consultant who creates winning strategies",
            "allow_delegation": True,
            "verbose": True,
            "tools": ["business_plan_generator", "swot_analysis_tool"],
            "max_iterations": 2,
        },
        "designer": {
            "role": "UI/UX Design Agent",
            "goal": "Create beautiful, functional interfaces",
            "backstory": "Creative designer specializing in SaaS products and user experiences",
            "allow_delegation": False,
            "verbose": False,
            "tools": ["brand_generator_tool", "wireframe_generator_tool", "ui_component_library"],
            "max_iterations": 3,
        },
        "developer": {
            "role": "Full Stack Developer Agent",
            "goal": "Build robust, production-ready code",
            "backstory": "Senior engineer with expertise across the full stack",
            "allow_delegation": False,
            "verbose": True,
            "tools": [
                "code_generator_tool",
                "code_review_tool",
                "test_generator_tool",
                "deployment_tool",
            ],
            "max_iterations": 4,
        },
        "marketer": {
            "role": "Marketing Agent",
            "goal": "Drive customer acquisition and brand awareness",
            "backstory": "Data-driven marketer with experience in growth hacking and digital marketing",
            "allow_delegation": True,
            "verbose": True,
            "tools": ["seo_tool", "content_generator_tool", "ad_optimizer_tool", "analytics_tool"],
            "max_iterations": 3,
        },
        "finance": {
            "role": "Financial Analyst Agent",
            "goal": "Manage financial planning and unit economics",
            "backstory": "CFA-level financial analyst specializing in startup economics",
            "allow_delegation": False,
            "verbose": True,
            "tools": [
                "financial_model_tool",
                "pricing_optimizer_tool",
                "revenue_forecaster",
                "unit_economics_calculator",
            ],
            "max_iterations": 3,
        },
        "support": {
            "role": "Customer Support Agent",
            "goal": "Build and manage support infrastructure",
            "backstory": "Customer experience expert who designs scalable support systems",
            "allow_delegation": False,
            "verbose": False,
            "tools": ["faq_generator_tool", "ticket_analyzer_tool", "sentiment_analyzer"],
            "max_iterations": 2,
        },
        "qa": {
            "role": "Quality Assurance Agent",
            "goal": "Ensure code quality and product reliability",
            "backstory": "Experienced QA lead who combines automated and manual testing",
            "allow_delegation": False,
            "verbose": True,
            "tools": ["test_runner_tool", "security_scanner", "performance_profiler"],
            "max_iterations": 3,
        },
    }


def get_manager_llm_config() -> Dict[str, Any]:
    """Get the manager LLM configuration for hierarchical CrewAI processes."""
    config: Dict[str, Any] = {
        "model": settings.LLM_MODEL or settings.OPENAI_MODEL or "gpt-4-turbo",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    # Add base_url for custom OpenAI-compatible providers
    base_url = settings.LLM_BASE_URL or ""
    if base_url:
        config["base_url"] = base_url
    # Add api_key if set
    api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY or ""
    if api_key:
        config["api_key"] = api_key
    return config


def get_crew_config(business_id: UUID, crew_type: str = "hierarchical") -> Dict[str, Any]:
    """Get full crew configuration for a business."""
    agent_configs = create_agent_configs(business_id)

    return {
        "agents": agent_configs,
        "process": crew_type,
        "manager_llm": get_manager_llm_config(),
        "max_rpm": 10,  # max requests per minute
        "memory": True,
        "verbose": True,
    }
