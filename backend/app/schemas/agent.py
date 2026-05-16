from typing import Optional

from pydantic import BaseModel, field_validator


class AgentConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    model_override: Optional[str] = None
    custom_prompt: Optional[str] = None
    temperature: Optional[float] = None

    @field_validator("temperature")
    @classmethod
    def validate_temp(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @field_validator("model_override")
    @classmethod
    def validate_model(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError("Model name too long (max 100)")
        return v


class AgentInfoResponse(BaseModel):
    name: str
    label: str
    description: str
    min_tier: str
    current_tier: str
    status: str  # "optimal" | "suboptimal" | "unknown"
    warning: str = ""
    enabled: bool = True
    model_override: str = ""
    custom_prompt: str = ""
    temperature: float = 0.7


class ModelInfoResponse(BaseModel):
    name: str
    tier: str
    params: str


class AgentListResponse(BaseModel):
    model: ModelInfoResponse
    agents: list[AgentInfoResponse]
