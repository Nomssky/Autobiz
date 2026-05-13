"""Auth middleware for JWT validation on all API routes."""
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED

from app.auth.jwt_handler import verify_token


class AuthMiddleware(BaseHTTPMiddleware):
    """Extract and validate JWT from Authorization header on API routes."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for non-API routes (docs, health, root)
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else auth_header.strip()

        if not token:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication token"},
            )

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