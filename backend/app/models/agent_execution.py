from sqlalchemy import Column, String, Integer, DateTime, Numeric, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from .base import BaseModel, GUID


class AgentExecution(BaseModel):
    """Log of all agent task executions for cost tracking and auditing"""

    __tablename__ = "agent_executions"

    business_id = Column(GUID(), ForeignKey("businesses.id"), nullable=False)
    role_name = Column(String(50), nullable=False)
    action = Column(String(255), nullable=True)
    input_tokens = Column(Integer, nullable=True, default=0)
    output_tokens = Column(Integer, nullable=True, default=0)
    cost_usd = Column(Numeric(10, 6), nullable=True, default=0.0)
    duration_ms = Column(Integer, nullable=True, default=0)
    success = Column(Boolean, nullable=False, default=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
