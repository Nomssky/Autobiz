from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.sql import func

from .base import GUID, BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    org_id = Column(GUID(), nullable=True, index=True)
    user_id = Column(GUID(), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    extra_data = Column("data", JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
