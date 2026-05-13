import pytest
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.agents.support import SupportAgent
from app.agents.base_agent import AgentResult


class TestSupportAgent(SupportAgent):
    def __init__(self, business_id):
        super().__init__(business_id, {'temperature': 0.7})

    async def execute_task(self, task_type, input_data, context=None):
        if task_type == 'unknown_task':
            return AgentResult(success=False, output=None, error='Unknown task type: unknown_task')
        return AgentResult(success=True, output={'task': task_type, 'data': input_data}, requires_approval=False)

    def get_tools(self):
        return []


@pytest.mark.asyncio
async def test_support_agent_initialization():
    business_id = uuid4()
    agent = TestSupportAgent(business_id)
    assert agent.business_id == business_id
    assert agent.role_name == 'support'
    assert agent.config == {'temperature': 0.7}


@pytest.mark.asyncio
async def test_support_agent_task_execution():
    business_id = uuid4()
    agent = TestSupportAgent(business_id)
    result = await agent.run_with_tracking('process_ticket', {
        'ticket_id': 'TKT-001',
        'customer_id': 'CUST-001',
        'subject': 'Login issue',
        'description': 'Cannot log in to account'
    })
    assert result.success is True
    assert result.output['task'] == 'process_ticket'
    assert result.execution_time_ms >= 0


@pytest.mark.asyncio
async def test_support_agent_unknown_task():
    business_id = uuid4()
    agent = TestSupportAgent(business_id)
    result = await agent.run_with_tracking('unknown_task', {})
    assert result.success is False
    assert 'Unknown task type' in result.error
