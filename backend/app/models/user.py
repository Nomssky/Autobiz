from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="ceo")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
