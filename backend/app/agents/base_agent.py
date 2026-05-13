from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from uuid import UUID
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

# ---- Real LLM integration with silent mock fallback ----

try:
    from langchain_openai import ChatOpenAI as _RealChatOpenAI
    from langchain_core.tools import Tool as _RealTool
    from langchain_core.messages import HumanMessage, SystemMessage

    class ChatOpenAI:
        def __init__(self, model: str, temperature: float, api_key: str):
            self._llm = _RealChatOpenAI(
                model=model or settings.OPENAI_MODEL,
                temperature=temperature or 0.7,
                api_key=api_key or settings.OPENAI_API_KEY,
            )
            self.model = model

        async def ainvoke(self, prompt: str, system_prompt: str = None) -> str:
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            result = await self._llm.ainvoke(messages)
            self.last_token_usage = {
                "input_tokens": result.usage_metadata.get("input_tokens", 0) if hasattr(result, "usage_metadata") else 0,
                "output_tokens": result.usage_metadata.get("output_tokens", 0) if hasattr(result, "usage_metadata") else 0,
            }
            return result.content

    Tool = _RealTool

except ImportError:
    logger.warning("langchain not installed — using mock LLM")

    class ChatOpenAI:
        def __init__(self, model: str, temperature: float, api_key: str):
            self.model = model
            self.temperature = temperature
            self.api_key = api_key

        async def ainvoke(self, prompt: str, system_prompt: str = None) -> str:
            return ""

    class Tool:
        def __init__(self, name: str, func, description: str):
            self.name = name
            self.func = func
            self.description = description

logger = logging.getLogger(__name__)


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
    
    def __init__(
        self,
        business_id: UUID,
        role_name: str,
        config: Dict[str, Any]
    ):
        self.business_id = business_id
        self.role_name = role_name
        self.config = config
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=config.get("temperature", 0.7),
            api_key=settings.OPENAI_API_KEY,
        )
        self.vector_store = None
        self.memory = {}
        
    @abstractmethod
    async def execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> AgentResult:
        """Execute a specific task for this agent role"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return list of tools available to this agent"""
        pass
    
    async def run_with_tracking(
        self,
        task_type: str,
        input_data: Dict[str, Any]
    ) -> AgentResult:
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
            return AgentResult(
                success=False,
                output=None,
                error=str(e)
            )
    
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