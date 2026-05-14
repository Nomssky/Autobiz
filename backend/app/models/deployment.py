from sqlalchemy import Column, DateTime, ForeignKey, String

from .base import GUID, JSONB, BaseModel


class Deployment(BaseModel):
    __tablename__ = "deployments"

    business_id = Column(GUID(), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    environment = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    changes = Column(JSONB(), nullable=True)
    triggered_by_role = Column(String(50), nullable=True)
    approved_by_ceo_id = Column(GUID(), nullable=True)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    rollback_at = Column(DateTime(timezone=True), nullable=True)
