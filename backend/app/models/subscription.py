from sqlalchemy import Column, String, Integer, DateTime, Numeric, Boolean
from sqlalchemy.sql import func
from .base import BaseModel, GUID


TIER_LIMITS = {
    "starter": {"businesses": 1, "ai_budget": 50.0, "price": 29},
    "growth": {"businesses": 5, "ai_budget": 200.0, "price": 99},
    "enterprise": {"businesses": None, "ai_budget": None, "price": None},
}


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    user_id = Column(GUID(), nullable=False, index=True)
    tier = Column(String(50), nullable=False, default="starter")
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    businesses_limit = Column(Integer, nullable=True)
    ai_budget_monthly = Column(Numeric(10, 2), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)

    def get_businesses_limit(self) -> int:
        if self.businesses_limit is not None:
            return self.businesses_limit
        limits = TIER_LIMITS.get(self.tier, TIER_LIMITS["starter"])
        return limits["businesses"] or 999999

    def get_ai_budget(self) -> float:
        if self.ai_budget_monthly is not None:
            return float(self.ai_budget_monthly)
        limits = TIER_LIMITS.get(self.tier, TIER_LIMITS["starter"])
        return limits["ai_budget"] or 999999.0

    def is_active(self) -> bool:
        return self.status == "active"
