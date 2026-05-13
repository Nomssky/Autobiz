from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class PricingTier(BaseModel):
    name: str
    price: float
    currency: str = "USD"
    billing_cycle: str = "monthly"
    features: List[str] = Field(default_factory=list)


class UnitEconomics(BaseModel):
    cac: float = Field(..., description="Customer acquisition cost")
    ltv: float = Field(..., description="Lifetime value")
    ltv_to_cac_ratio: float
    payback_months: float
    gross_margin: float = 0.75


class MonthlyProjection(BaseModel):
    month: int
    revenue: float
    cost: float
    profit: float
    cumulative_profit: float


class FinanceOutput(BaseModel):
    pricing_tiers: List[PricingTier] = Field(default_factory=list)
    unit_economics: Optional[UnitEconomics] = None
    setup_cost: float = Field(default=2500.0)
    monthly_burn_rate: float = Field(default=5000.0)
    runway_months: int = Field(default=12)
    break_even_date: Optional[date] = None
    break_even_month: int = Field(default=6)
    projected_revenue_month_12: float = Field(default=100000.0)
    funding_needed: float = Field(default=0.0)
    monthly_projections: List[MonthlyProjection] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
