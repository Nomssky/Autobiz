from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from .base import GUID, BaseModel


class Business(BaseModel):
    __tablename__ = "businesses"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    ceo_id = Column(GUID(), nullable=False)
    status = Column(String(50), nullable=False, default="building")
    current_phase = Column(String(50), nullable=False, default="initialization")
    business_metadata = Column(JSON, nullable=False, default={})
    extra_metadata = Column(JSON, nullable=False, default={})
    config = Column(JSON, nullable=True, default={})
    launched_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    tasks = relationship("AgentTask", back_populates="business", lazy="selectin")
