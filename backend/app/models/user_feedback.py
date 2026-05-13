from sqlalchemy import Column, String, Text, DateTime, Numeric, Boolean, ForeignKey
from .base import BaseModel, GUID

class UserFeedback(BaseModel):
    __tablename__ = "user_feedback"
    
    business_id = Column(GUID(), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), nullable=True)
    feedback_type = Column(String(50), nullable=True)  # bug, feature_request, praise, complaint
    content = Column(Text, nullable=False)
    sentiment_score = Column(Numeric(3, 2), nullable=True)  # -1 to 1
    processed_by_ai = Column(Boolean, nullable=False, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    action_taken = Column(Text, nullable=True)