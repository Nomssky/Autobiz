from sqlalchemy import Boolean, Column, Numeric, String, Text

from .base import GUID, BaseModel


class AgentConfig(BaseModel):
    __tablename__ = "agent_configs"

    user_id = Column(GUID(), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    model_override = Column(String(100), nullable=True)
    custom_prompt = Column(Text, nullable=True)
    temperature = Column(Numeric(3, 2), nullable=True)
