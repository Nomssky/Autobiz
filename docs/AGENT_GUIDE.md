# AutoBiz Engine — Agent Guide

This guide covers how AI agents work in AutoBiz Engine and how to customize them.

## Agent Roles

| Role | Responsibility | Default Model |
|------|---------------|---------------|
| Researcher | Market analysis, competitor research, trend analysis | GPT-4 |
| Developer | Code generation, bug fixes, feature implementation | GPT-4 |
| Designer | Image generation, branding, UI/UX | DALL-E / Replicate |
| Marketer | Social media, blog posts, email campaigns, launch strategy | GPT-4 |
| Finance | Pricing, payments, revenue tracking, invoicing | GPT-4 |
| Support | Ticket processing, auto-responses, sentiment analysis | GPT-3.5 |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 TaskDistributor                 │
│  (Routes tasks to agents based on type/priority) │
└──────────┬──────────┬──────────┬───────────────┘
           │          │          │
     ┌─────▼──┐ ┌────▼────┐ ┌──▼──────────┐
     │Researcher│ │Developer│ │  Designer   │
     └─────────┘ └─────────┘ └─────────────┘
           │          │          │
     ┌─────▼─────┐ ┌─▼────────┐ │
     │ Marketer  │ │ Finance  │ │
     └───────────┘ └──────────┘ │
                        ┌───────▼───────┐
                        │   Support     │
                        └───────────────┘
```

## Base Agent Class

All agents inherit from `BaseAgent` (`app/agents/base_agent.py`):

```python
class BaseAgent:
    """Base class for all AI agents."""
    
    def __init__(self, role: str, model: str = None):
        self.role = role
        self.model = model or settings.OPENAI_MODEL
        self.execution_history: List[AgentResult] = []
    
    async def run_with_tracking(self, task_type: str, input_data: Dict) -> AgentResult:
        """Execute task with token tracking and cost calculation."""
        ...
    
    async def run(self, task_type: str, input_data: Dict) -> str:
        """Execute task and return result as text."""
        ...
```

## Creating a Custom Agent

### Step 1: Create the agent file

```python
# app/agents/my_custom_agent.py

from app.agents.base_agent import BaseAgent, AgentResult
from typing import Dict, Any

class MyCustomAgent(BaseAgent):
    """Custom agent for specialized tasks."""
    
    def __init__(self):
        super().__init__(role="custom_agent")
    
    def _build_prompt(self, task_type: str, input_data: Dict[str, Any]) -> str:
        return f"""
        You are a specialized assistant for {task_type}.
        
        Context: {input_data.get('context', 'N/A')}
        Task: {input_data.get('task', 'Complete the task')}
        
        Provide a detailed response.
        """
    
    async def execute(self, task_type: str, input_data: Dict[str, Any]) -> str:
        prompt = self._build_prompt(task_type, input_data)
        return await self.run(task_type, {"prompt": prompt})
```

### Step 2: Register with TaskDistributor

Edit the `TASK_ROUTING` dict in `app/orchestrator/task_distributor.py`:

```python
TASK_ROUTING = {
    ...
    "my_custom_task": "custom_agent",  # Add this line
}
```

### Step 3: Add to agent pool

Wherever you initialize agents, add your custom agent:

```python
from app.agents.my_custom_agent import MyCustomAgent

agent_pool = {
    ...
    "custom_agent": MyCustomAgent(),
}
```

## Agent Task Types

### Standard Task Types

| Task Type | Agent | Description |
|-----------|-------|-------------|
| `validate_business_idea` | researcher | Validate market need |
| `market_analysis` | researcher | Analyze market size & competitors |
| `competitor_research` | researcher | Research competitors |
| `trend_analysis` | researcher | Identify industry trends |
| `generate_application` | developer | Generate application code |
| `fix_bug` | developer | Fix reported bugs |
| `implement_feature` | developer | Implement new features |
| `deploy` | developer | Deployment scripts & configs |
| `generate_image` | designer | Generate images via DALL-E/Replicate |
| `create_logo` | designer | Logo design |
| `design_banner` | designer | Marketing banners |
| `create_brand_identity` | designer | Full brand identity |
| `create_social_post` | marketer | Social media content |
| `write_blog_post` | marketer | Blog articles |
| `create_email_campaign` | marketer | Email sequences |
| `setup_pricing_and_payments` | finance | Pricing strategy + Stripe setup |
| `track_revenue` | finance | Revenue monitoring |
| `process_ticket` | support | Customer support tickets |

### Custom Task Types

Add new task types by:
1. Defining the task in `TASK_ROUTING`
2. Implementing the agent
3. Adding the task type in `AgentTask` status tracking

## Multi-Agent Collaboration (CrewAI)

For complex workflows, agents can collaborate via CrewAI:

```python
from crewai import Crew, Process
from agents.crew_tasks import research_task, dev_task

crew = Crew(
    agents=[researcher, developer],
    tasks=[research_task, dev_task],
    process=Process.hierarchical,
    manager_llm=ChatOpenAI(model="gpt-4")
)

result = crew.kickoff()
```

Configuration: `configs/crew_config.yaml`

## Prompt Engineering

All agents use system prompts defined per role. To customize:

1. Locate the agent file in `app/agents/`
2. Find the `_build_prompt()` method
3. Modify the system prompt template

### Prompt Template Variables

```python
SYSTEM_PROMPT = """
You are a {role} agent for AutoBiz Engine.
Business: {business_name}
Current Phase: {current_phase}
Industry: {industry}

Follow these rules:
1. Provide actionable, specific recommendations
2. Include code examples where relevant
3. Cite sources for market data
4. Be concise but thorough
"""
```

## Monitoring Agent Performance

Track agent execution quality:

```python
from app.infrastructure.query_optimizer import get_query_stats

# Get execution statistics
stats = get_query_stats()
print(f"Total queries: {stats['total_unique_queries']}")
for q in stats['queries'][:5]:
    print(f"  {q['query'][:60]}... → avg {q['avg_ms']}ms")
```

## Testing Agents

Run agent tests:

```bash
# All agent tests
pytest tests/ -k "agent" -v

# Specific agent
pytest tests/test_researcher_agent.py -v
pytest tests/test_developer_agent.py -v
pytest tests/test_finance_agent.py -v

# All tests
pytest tests/ -v --tb=short
```