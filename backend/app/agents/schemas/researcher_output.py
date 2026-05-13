from pydantic import BaseModel, Field
from typing import List, Optional


class Competitor(BaseModel):
    name: str = Field(..., description="Competitor company name")
    market_share: Optional[float] = Field(None, description="Estimated market share percentage")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    pricing: Optional[str] = None


class ResearcherOutput(BaseModel):
    business_name: str = Field(..., description="Generated business name")
    market_size_usd: float = Field(..., description="Total addressable market in USD")
    competitors: List[Competitor] = Field(default_factory=list)
    opportunity_score: float = Field(..., ge=0, le=100, description="Market opportunity score 0-100")
    recommended_positioning: str = Field(..., description="Recommended market positioning strategy")
    target_audience: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    estimated_cac: float = Field(default=50.0, description="Estimated customer acquisition cost")
    estimated_ltv: float = Field(default=500.0, description="Estimated lifetime value")
    business_model: str = Field(default="saas", description="Recommended business model")
    brand_personality: str = Field(default="professional")
    usp: List[str] = Field(default_factory=list, description="Unique selling points")
    description: str = Field(default="", description="Business description")
    risk_factors: List[str] = Field(default_factory=list)
