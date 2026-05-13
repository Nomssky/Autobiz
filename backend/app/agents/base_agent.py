from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from uuid import UUID
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# ---- Real LLM integration with mock fallback ----

try:
    from langchain_openai import ChatOpenAI as _RealChatOpenAI
    from langchain_core.tools import Tool as _RealTool
    from langchain_core.messages import HumanMessage, SystemMessage

    class ChatOpenAI:
        def __init__(self, model: str, temperature: float, api_key: str):
            self._llm = _RealChatOpenAI(
                model=model or "gpt-4-turbo",
                temperature=temperature or 0.7,
                api_key=api_key,
            )
            self.model = model

        async def ainvoke(self, prompt: str, system_prompt: str = None) -> str:
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            result = await self._llm.ainvoke(messages)
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
            prefix = system_prompt[:50] if system_prompt else ""
            return f"Mock response for: {prefix}...{prompt[:50]}..."

    class Tool:
        def __init__(self, name: str, func, description: str):
            self.name = name
            self.func = func
            self.description = description

# ---- CrewAI integration ----

try:
    from crewai import Agent as _CrewAgent, Task as _CrewTask, Crew as _Crew

    class CrewAgent:
        @staticmethod
        def create(role: str, goal: str, backstory: str, tools: list, llm: Any) -> Any:
            return _CrewAgent(
                role=role,
                goal=goal,
                backstory=backstory,
                tools=tools,
                llm=llm._llm if hasattr(llm, '_llm') else None,
                verbose=True,
            )

    class CrewTask:
        @staticmethod
        def create(description: str, expected_output: str, agent: Any) -> Any:
            return _CrewTask(
                description=description,
                expected_output=expected_output,
                agent=agent,
            )

    class CrewRunner:
        @staticmethod
        async def run(crew: Any) -> str:
            return await crew.kickoff_async()

except ImportError:
    logger.warning("crewai not installed — using mock CrewAI")

    class CrewAgent:
        @staticmethod
        def create(role: str, goal: str, backstory: str, tools: list, llm: Any) -> Any:
            return type("obj", (object,), {"role": role})()

    class CrewTask:
        @staticmethod
        def create(description: str, expected_output: str, agent: Any) -> Any:
            return type("obj", (object,), {"description": description})()

    class CrewRunner:
        @staticmethod
        async def run(crew: Any) -> str:
            return "Mock crew execution complete"

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
        # In a real app, we would get these from settings
        self.llm = ChatOpenAI(
            model="gpt-4-turbo",
            temperature=config.get("temperature", 0.7),
            api_key="mock-api-key"
        )
        # Placeholder for vector store and memory
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