"""
Rate Limiting & Webhook Security Middleware
"""
import time
import hmac
import hashlib
import logging
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.config import settings

logger = logging.getLogger("security")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding window rate limiter.
    Limits per-IP request rate to prevent abuse.

    Default: 100 requests per 60 seconds.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for internal/health endpoints
        if request.url.path.startswith(("/health", "/metrics")):
            return await call_next(request)

        current_time = time.time()
        window_start = current_time - self.window_seconds

        # Clean old entries
        if client_ip in self._requests:
            self._requests[client_ip] = [
                t for t in self._requests[client_ip] if t > window_start
            ]
        else:
            self._requests[client_ip] = []

        # Check limit
        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.max_requests} requests per {self.window_seconds}s",
                },
            )

        self._requests[client_ip].append(current_time)
        return await call_next(request)


class WebhookAuthMiddleware(BaseHTTPMiddleware):
    """
    Validates webhook requests using HMAC signature verification.

    Expects header: X-Webhook-Signature: sha256=<hmac_sha256_hex>
    Computes HMAC using WEBHOOK_SECRET from settings.
    """

    def __init__(self, app, secret: Optional[str] = None):
        super().__init__(app)
        self.secret = secret or settings.SECRET_KEY

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only validate webhook endpoints
        if not request.url.path.startswith("/api/v1/webhooks"):
            return await call_next(request)

        signature_header = request.headers.get("X-Webhook-Signature", "")

        if not signature_header.startswith("sha256="):
            logger.warning("Webhook request missing valid signature")
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid webhook signature"},
            )

        provided_signature = signature_header.split("sha256=")[1]

        # Read raw body for signature verification
        raw_body = await request.body()
        expected_signature = hmac.new(
            key=self.secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(provided_signature, expected_signature):
            logger.warning("Webhook signature verification failed")
            return JSONResponse(
                status_code=401,
                content={"error": "Webhook signature verification failed"},
            )

        logger.info(f"Webhook signature verified from {request.client.host if request.client else 'unknown'}")
        return await call_next(request)