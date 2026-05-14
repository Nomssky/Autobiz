import os
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.agents.base_agent import AgentResult, BaseAgent


# Concrete implementation for testing
class TestAgent(BaseAgent):
    async def execute_task(
        self, task_type: str, input_data: dict, context: dict = None
    ) -> AgentResult:
        return AgentResult(
            success=True, output={"task": task_type, "data": input_data}, requires_approval=False
        )

    def get_tools(self) -> list:
        return []


@pytest.mark.asyncio
async def test_base_agent_initialization():
    business_id = uuid4()
    config = {"temperature": 0.8}
    agent = TestAgent(business_id, "tester", config)

    assert agent.business_id == business_id
    assert agent.role_name == "tester"
    assert agent.config == config


@pytest.mark.asyncio
async def test_agent_task_execution():
    business_id = uuid4()
    agent = TestAgent(business_id, "tester", {})

    result = await agent.run_with_tracking("test_task", {"param": "value"})

    assert result.success is True
    assert result.output["task"] == "test_task"
    assert result.output["data"] == {"param": "value"}
    assert result.execution_time_ms >= 0
