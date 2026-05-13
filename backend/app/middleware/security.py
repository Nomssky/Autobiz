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

try:
    import redis as _redis

    def _get_redis():
        try:
            return _redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2, decode_responses=True)
        except Exception:
            return None
except ImportError:
    def _get_redis():
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter with Redis backend + in-memory fallback."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._local: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        if request.url.path.startswith(("/health", "/metrics")):
            return await call_next(request)

        r = _get_redis()
        if r:
            try:
                key = f"ratelimit:{client_ip}"
                now = int(time.time())
                window_start = now - self.window_seconds
                r.zremrangebyscore(key, 0, window_start)
                count = r.zcard(key)
                if count is not None and count >= self.max_requests:
                    return JSONResponse(status_code=429, content={"detail": "Too many requests"})
                r.zadd(key, {str(now): now})
                r.expire(key, self.window_seconds)
                return await call_next(request)
            except Exception:
                r = None
        if r is None:
            now = time.time()
            window_start = now - self.window_seconds
            if client_ip in self._local:
                self._local[client_ip] = [t for t in self._local[client_ip] if t > window_start]
            else:
                self._local[client_ip] = []
            if len(self._local[client_ip]) >= self.max_requests:
                return JSONResponse(status_code=429, content={"detail": "Too many requests"})
            self._local[client_ip].append(now)

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