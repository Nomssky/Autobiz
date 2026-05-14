import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from app.config import settings
from app.agents.llm_factory import create_llm
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# ---- Tool import with graceful fallback ----

try:
    from langchain_core.tools import Tool
except ImportError:
    logger.warning("langchain-core not installed — using mock Tool class")

    class Tool:
        def __init__(self, name: str, func, description: str):
            self.name = name
            self.func = func
            self.description = description


class AgentResult(BaseModel):
    success: bool
    output: Any
    requires_approval: bool = False
    approval_proposal: Optional[Dict] = None
    error: Optional[str] = None
    tokens_used: Dict[str, int] = {}
    execution_time_ms: int = 0

    def validate_output(self, schema: Type[BaseModel]) -> BaseModel:
        if not self.success or self.output is None:
            raise ValueError("Cannot validate failed agent output")
        try:
            if isinstance(self.output, dict):
                return schema.model_validate(self.output)
            return schema.model_validate(self.output)
        except ValidationError as e:
            logger.error(f"Output validation failed: {e}")
            raise


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""

    def __init__(self, business_id: UUID, role_name: str, config: Dict[str, Any]):
        self.business_id = business_id
        self.role_name = role_name
        self.config = config
        self.llm = create_llm(
            model=config.get("model"),
            temperature=config.get("temperature"),
            api_key=config.get("api_key"),
        )
        self.vector_store = None
        self.memory = {}

    @abstractmethod
    async def execute_task(
        self, task_type: str, input_data: Dict[str, Any], context: Optional[Dict] = None
    ) -> AgentResult:
        """Execute a specific task for this agent role"""
        pass

    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return list of tools available to this agent"""
        pass

    async def run_with_tracking(self, task_type: str, input_data: Dict[str, Any]) -> AgentResult:
        """Run task with logging, token tracking, and error handling"""
        start_time = datetime.now()

        try:
            result = await self.execute_task(task_type, input_data)

            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            result.execution_time_ms = duration_ms

            # Estimate tokens if not set by agent
            if not result.tokens_used:
                output_str = str(result.output or "")
                input_str = str(input_data or "")
                result.tokens_used = {
                    "input_tokens": len(input_str) // 4,
                    "output_tokens": len(output_str) // 4,
                }

            return result

        except Exception as e:
            logger.error(f"Agent {self.role_name} failed: {str(e)}", exc_info=True)
            return AgentResult(success=False, output=None, error=str(e))

    async def save_to_memory(self, key: str, value: Any, metadata: Dict = None):
        """Save important context to vector memory"""
        self.memory[key] = {"value": value, "metadata": metadata or {}}

    async def retrieve_from_memory(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant context from memory"""
        # Simple mock: return memories that have the query in the key
        results = []
        for key, value in self.memory.items():
            if query.lower() in key.lower():
                results.append(value)
        return results[:limit]
