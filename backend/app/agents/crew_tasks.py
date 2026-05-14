"""CrewAI task definitions for all agent roles."""

from typing import Any, Dict


def create_research_task(idea: str, business_name: str) -> Dict[str, Any]:
    """Create market research task for CrewAI."""
    return {
        "role": "Market Researcher",
        "goal": f"Conduct comprehensive market research for '{business_name}'",
        "backstory": (
            "You are an expert market researcher with deep knowledge of "
            "industry analysis, competitor research, and market sizing."
        ),
        "task": (
            f"Research the market for a business idea: '{idea}'. "
            f"Provide: 1) Market size estimation (TAM/SAM/SOM), "
            f"2) Top 5 competitors with strengths/weaknesses, "
            f"3) Target audience segmentation, "
            f"4) Key market trends and opportunities, "
            f"5) Potential risks and challenges."
        ),
        "expected_output": "A detailed market research report in JSON format with sections for market_size, competitors, audience, trends, and risks.",
        "tools": ["web_search", "competitor_analysis"],
    }


def create_business_plan_task(idea: str, research: Dict) -> Dict[str, Any]:
    """Create business plan generation task for CrewAI."""
    return {
        "role": "Business Strategist",
        "goal": "Generate a comprehensive business plan with go-to-market strategy",
        "backstory": (
            "You are a seasoned business strategist who has helped dozens of "
            "startups go from idea to execution."
        ),
        "task": (
            f"Create a detailed business plan for: '{idea}'. "
            f"Include: 1) Executive summary, 2) Value proposition, "
            f"3) Revenue model, 4) Go-to-market strategy, "
            f"5) 12-month roadmap with milestones, "
            f"6) Required resources and team composition."
        ),
        "expected_output": "Business plan in structured JSON format with sections for summary, strategy, roadmap, and resources.",
    }


def create_design_task(idea: str, business_name: str) -> Dict[str, Any]:
    """Create UI/UX design task for CrewAI."""
    return {
        "role": "UI/UX Designer",
        "goal": f"Design the user interface and experience for '{business_name}'",
        "backstory": (
            "You are an expert UI/UX designer with experience in creating "
            "modern, user-friendly interfaces for SaaS products."
        ),
        "task": (
            f"Design the UI/UX for '{business_name}'. Provide: "
            f"1) Color palette and typography, "
            f"2) Wireframe descriptions for key pages (landing, dashboard, settings), "
            f"3) Component library, 4) User flow diagrams, "
            f"5) Accessibility guidelines."
        ),
        "expected_output": "Design specification document in JSON format with color_scheme, typography, wireframes, components, and user_flows.",
    }


def create_development_task(
    idea: str, tech_stack: str = "Python, FastAPI, React"
) -> Dict[str, Any]:
    """Create application development task for CrewAI."""
    return {
        "role": "Full Stack Developer",
        "goal": "Build a fully functional application with backend and frontend",
        "backstory": (
            "You are a senior full-stack developer proficient in multiple "
            "frameworks and best practices."
        ),
        "task": (
            f"Build a web application for: '{idea}'. "
            f"Tech stack: {tech_stack}. "
            f"Provide: 1) Project structure, 2) Database schema, "
            f"3) API endpoints specification, 4) Frontend component structure, "
            f"5) Authentication flow, 6) Deployment configuration."
        ),
        "expected_output": "Complete code architecture document in JSON format with project_structure, database_schema, api_spec, frontend_components, and deployment_config.",
    }


def create_marketing_task(business_name: str, target_audience: str) -> Dict[str, Any]:
    """Create marketing strategy task for CrewAI."""
    return {
        "role": "Digital Marketing Strategist",
        "goal": f"Create a comprehensive marketing strategy for '{business_name}'",
        "backstory": (
            "You are a data-driven digital marketing strategist with expertise "
            "in SEO, content marketing, social media, and paid advertising."
        ),
        "task": (
            f"Create a marketing strategy for '{business_name}' targeting {target_audience}. "
            f"Include: 1) Brand positioning, 2) Content calendar for 3 months, "
            f"3) SEO strategy with keywords, 4) Social media plan, "
            f"5) Paid advertising budget allocation, 6) KPIs and metrics."
        ),
        "expected_output": "Marketing strategy document in JSON format with positioning, content_calendar, seo_strategy, social_media_plan, and budget_allocation.",
    }


def create_finance_task(monthly_budget: float) -> Dict[str, Any]:
    """Create financial modeling task for CrewAI."""
    return {
        "role": "Financial Analyst",
        "goal": "Build financial models and projections",
        "backstory": (
            "You are a certified financial analyst specializing in startup "
            "financial modeling and unit economics."
        ),
        "task": (
            f"Build a comprehensive financial model with monthly budget of ${monthly_budget:.2f}. "
            f"Include: 1) Revenue projections for 12 months, "
            f"2) Cost breakdown and burn rate analysis, "
            f"3) Break-even analysis, 4) Cash flow projections, "
            f"5) Key financial metrics (CAC, LTV, ROI, runway)."
        ),
        "expected_output": "Financial model in JSON format with projections, cost_analysis, break_even, cash_flow, and key_metrics.",
    }


def create_support_task(product_description: str) -> Dict[str, Any]:
    """Create customer support strategy task for CrewAI."""
    return {
        "role": "Customer Support Lead",
        "goal": "Design customer support systems and processes",
        "backstory": (
            "You are an experienced customer support leader who has built "
            "support organizations from the ground up."
        ),
        "task": (
            f"Design a customer support system for: '{product_description}'. "
            f"Include: 1) Support channels setup, 2) Response time SLAs, "
            f"3) Knowledge base structure, 4) Escalation procedures, "
            f"5) Customer satisfaction metrics, 6) AI-powered support integration."
        ),
        "expected_output": "Support system design in JSON format with channels, slas, knowledge_base, escalation, and ai_integration.",
    }


# Process types for CrewAI hierarchical flow
PROCESS_TYPES = {
    "sequential": "Tasks executed one after another",
    "hierarchical": "Manager-led task delegation with review",
    "collaborative": "Parallel execution with inter-agent communication",
}
