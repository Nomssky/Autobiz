from sqlalchemy import Column, String, Integer, DateTime, Numeric, ForeignKey
from .base import BaseModel, GUID, JSONB

class MetricSnapshot(BaseModel):
    __tablename__ = "metrics_snapshots"
    
    business_id = Column(GUID(), ForeignKey("businesses.id"), nullable=False)
    recorded_by_role = Column(String(50), nullable=False)
    daily_revenue = Column(Numeric(10, 2), nullable=True)
    weekly_revenue = Column(Numeric(10, 2), nullable=True)
    monthly_revenue = Column(Numeric(10, 2), nullable=True)
    users_count = Column(Integer, nullable=True)
    active_users_count = Column(Integer, nullable=True)
    churn_rate = Column(Numeric(5, 4), nullable=True)
    bug_count = Column(Integer, nullable=True)
    support_tickets_count = Column(Integer, nullable=True)
    open_support_tickets = Column(Integer, nullable=True)
    conversion_rate = Column(Numeric(5, 4), nullable=True)
    customer_acquisition_cost = Column(Numeric(10, 2), nullable=True)
    lifetime_value = Column(Numeric(10, 2), nullable=True)
    custom_metrics = Column(JSONB(), nullable=True)