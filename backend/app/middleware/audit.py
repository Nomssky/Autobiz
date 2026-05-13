"""Audit logging middleware — records key actions to audit_logs table."""
import json
import logging
from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.database import SessionLocal
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

AUDIT_ACTIONS = {
    "POST /api/v1/businesses/create": "business.create",
    "DELETE /api/v1/businesses/": "business.archive",
    "POST /api/v1/businesses/": ("business.launch", "business.update"),
    "POST /api/v1/approvals/": "approval.create",
    "POST /api/v1/approvals/": "approval.decide",
    "DELETE /api/v1/approvals/": "approval.cancel",
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs mutating API calls to the audit_logs table."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.url.path.startswith("/api/v1"):
            user_id = getattr(request.state, "user_id", None)
            if user_id and response.status_code < 400:
                try:
                    action = f"{request.method} {request.url.path}".split("?")[0]
                    db = SessionLocal()
                    try:
                        log = AuditLog(
                            user_id=UUID(user_id) if user_id else None,
                            action=action,
                            resource_type=request.url.path.split("/")[3] if len(request.url.path.split("/")) > 3 else None,
                            ip_address=request.client.host if request.client else None,
                        )
                        db.add(log)
                        db.commit()
                    except Exception:
                        pass
                    finally:
                        db.close()
                except Exception:
                    pass

        return response
