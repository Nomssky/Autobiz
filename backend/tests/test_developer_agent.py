import pytest
import sys
import os
from uuid import uuid4

# Add the root directory to the path so we can import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.agents.developer import DeveloperAgent

# Mock TestAgent that inherits from DeveloperAgent for testing
class TestDeveloperAgent(DeveloperAgent):
    def __init__(self, business_id: UUID):
        # Call parent constructor with minimal config
        super().__init__(business_id, {"temperature": 0.7})
    
    async def execute_task(self, task_type: str, input_data: dict, context: dict = None):
        # Mock implementation that just returns success
        from backend.app.agents.base_agent import AgentResult
        return AgentResult(
            success=True,
            output={"task": task_type, "data": input_data},
            requires_approval=False
        )
    
    def get_tools(self):
        return []

@pytest.mark.asyncio
async def test_developer_agent_initialization():
    business_id = uuid4()
    agent = TestDeveloperAgent(business_id)
    
    assert agent.business_id == business_id
    assert agent.role_name == "developer"
    assert agent.config == {"temperature": 0.7}

@pytest.mark.asyncio
async def test_developer_agent_task_execution():
    business_id = uuid4()
    agent = TestDeveloperAgent(business_id)
    
    result = await agent.run_with_tracking("generate_application", {
        "business_name": "Test Business",
        "description": "A test business",
        "features": ["feature1", "feature2"]
    })
    
    assert result.success is True
    assert result.output["task"] == "generate_application"
    assert result.output["data"]["business_name"] == "Test Business"
    assert result.execution_time_ms >= 0