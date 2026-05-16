from typing import Generator, List
from uuid import UUID

from app.database import SessionLocal
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

# ---- Database Engine & Session ----


def get_db_session() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---- Auth ----


def get_current_user(request: Request) -> UUID:
    """Extract the authenticated user's UUID from the request state (set by AuthMiddleware)."""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        return UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )


def require_ceo(
    request: Request,
    ceo_id: UUID = Depends(get_current_user),
) -> UUID:
    """Dependency that ensures the current user has CEO role."""
    user_roles = getattr(request.state, "roles", [])
    if "ceo" in user_roles:
        return ceo_id
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="CEO role required",
    )


def require_role(allowed_roles: List[str]):
    """Factory for role-based access control.

    Usage:
        @router.delete("/{id}")
        async def archive(user=Depends(require_role(["owner", "admin"]))):
            ...
    """

    def _require_role(
        request: Request,
        db: Session = Depends(get_db_session),
        current_user: UUID = Depends(get_current_user),
    ) -> UUID:
        from app.models.organization import OrgMembership

        user_roles = getattr(request.state, "roles", [])
        if "ceo" in user_roles:
            return current_user

        membership = db.execute(
            select(OrgMembership).where(OrgMembership.user_id == current_user)
        ).scalar_one_or_none()

        if membership and membership.role in allowed_roles:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return _require_role
