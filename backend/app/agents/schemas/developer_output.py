from typing import List, Optional

from pydantic import BaseModel, Field


class Feature(BaseModel):
    name: str
    description: str
    priority: str = "medium"


class TechDecision(BaseModel):
    category: str
    choice: str
    rationale: str


class DeveloperOutput(BaseModel):
    tech_stack: List[str] = Field(..., description="Selected technology stack")
    architecture_summary: str = Field(..., description="High-level architecture description")
    features: List[Feature] = Field(default_factory=list)
    timeline_weeks: int = Field(default=4, ge=1, le=52)
    estimated_cost_usd: float = Field(default=5000.0)
    staging_url: Optional[str] = None
    production_url: Optional[str] = None
    version: str = Field(default="1.0.0")
    ready_for_deployment: bool = False
    decisions: List[TechDecision] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
