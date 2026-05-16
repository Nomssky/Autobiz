"""Auth middleware for JWT and API Key validation on all API routes."""

from app.auth.jwt_handler import verify_token
from app.database import SessionLocal
from app.api.v1.api_keys import verify_api_key
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED

PUBLIC_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/webhooks"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Extract and validate JWT or API Key from Authorization header."""

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        if any(request.url.path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = (
            auth_header.removeprefix("Bearer ").strip()
            if auth_header.startswith("Bearer ")
            else auth_header.strip()
        )

        if not token:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication token"},
            )

        # API Key auth (prefix: ab_)
        if token.startswith("ab_"):
            db = SessionLocal()
            try:
                result = verify_api_key(token, db)
                if result is None:
                    return JSONResponse(
                        status_code=HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid or revoked API key"},
                    )
                user_id, permissions = result
                request.state.user_id = str(user_id)
                request.state.roles = ["ceo"]
            finally:
                db.close()
        else:
            # JWT auth
            payload = verify_token(token)
            if not payload:
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"},
                )
            request.state.user_id = payload.get("sub")
            request.state.roles = payload.get("roles", [])

        response = await call_next(request)
        return response
