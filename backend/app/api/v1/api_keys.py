import secrets
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.api.dependencies import get_db_session, get_current_user, require_role
from app.models.base import BaseModel, GUID
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func


class ApiKey(BaseModel):
    __tablename__ = "api_keys"

    org_id = Column(GUID(), nullable=True, index=True)
    user_id = Column(GUID(), nullable=False)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(8), nullable=False)
    key_hash = Column(String(128), nullable=False)
    permissions = Column(Text, nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", summary="Create API key")
def create_api_key(
    name: str,
    permissions: str = "read",
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user),
):
    raw_key = f"ab_{secrets.token_hex(24)}"
    key_prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = ApiKey(
        user_id=user_id,
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        permissions=permissions,
    )
    db.add(api_key)
    db.flush()

    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "key": raw_key,
        "key_prefix": key_prefix,
        "permissions": permissions,
        "warning": "Save this key — it will not be shown again",
    }


@router.get("/", summary="List API keys")
def list_api_keys(
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user),
):
    keys = db.execute(
        select(ApiKey).where(
            ApiKey.user_id == user_id,
            ApiKey.is_active == True,
        )
    ).scalars().all()

    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "permissions": k.permissions,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        }
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke API key")
def revoke_api_key(
    key_id: UUID,
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user),
):
    key = db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
    ).scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.is_active = False
    return


def verify_api_key(key: str, db: Session) -> tuple[UUID, str] | None:
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    api_key = db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
        )
    ).scalar_one_or_none()

    if not api_key:
        return None

    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None

    api_key.last_used_at = datetime.utcnow()
    return api_key.user_id, api_key.permissions
