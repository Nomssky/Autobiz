from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from .base import GUID, BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=False, default="starter")
    owner_id = Column(GUID(), nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=True)


class OrgMembership(BaseModel):
    __tablename__ = "org_memberships"

    org_id = Column(GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID(), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")

    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_user"),)
