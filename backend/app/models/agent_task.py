from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel, GUID, JSONB

class AgentTask(BaseModel):
    __tablename__ = "ai_tasks"

    business = relationship("Business", back_populates="tasks")
    
    business_id = Column(GUID(), ForeignKey("businesses.id"), nullable=False)
    role_name = Column(String(50), nullable=False)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    input_data = Column(JSONB(), nullable=True)
    output_data = Column(JSONB(), nullable=True)
    error_message = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=1)
    requires_approval = Column(Boolean, nullable=False, default=False)
    approved_by_ceo_at = Column(DateTime(timezone=True), nullable=True)
    approval_request_id = Column(GUID(), ForeignKey("approval_requests.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)