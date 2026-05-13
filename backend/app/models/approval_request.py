from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from .base import BaseModel, GUID, JSONB

class ApprovalRequest(BaseModel):
    __tablename__ = "approval_requests"
    
    business_id = Column(GUID(), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(GUID(), ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    proposed_changes = Column(JSONB(), nullable=False)
    impact_analysis = Column(JSONB(), nullable=True)
    urgency = Column(String(50), nullable=False, default='normal')  # low, normal, high, critical
    status = Column(String(50), nullable=False, default='pending')  # pending, approved, rejected, expired
    ceo_decision = Column(Text, nullable=True)
    decided_by_ceo_id = Column(GUID(), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)