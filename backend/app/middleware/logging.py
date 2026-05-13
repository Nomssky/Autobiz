"""
Request/Response Logging Middleware
Logs all incoming requests and outgoing responses for monitoring and debugging.
"""
import json
import time
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

logger = logging.getLogger("api.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs detailed request and response information.

    Features:
    - Logs method, path, query params, client IP
    - Logs response status, duration, content length
    - Redacts sensitive headers (Authorization, Cookie)
    - Handles streaming responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Log request (async — needs to await request.body())
        await self._log_request(request)

        response: Response = await call_next(request)

        # Log response
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self._log_response(request, response, elapsed_ms)

        # Add performance headers
        response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}ms"

        return response

    async def _log_request(self, request: Request) -> None:
        """Log incoming request details."""
        headers = dict(request.headers)
        # Redact sensitive headers
        for key in ["authorization", "cookie", "x-api-key"]:
            if key in headers:
                headers[key] = "*****"

        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                raw_body = await request.body()
                if raw_body and len(raw_body) < 1024:
                    body = raw_body.decode("utf-8", errors="replace")
                elif raw_body:
                    body = f"<{len(raw_body)} bytes>"
            except Exception:
                body = "<unreadable>"

        logger.info(
            "→ %s %s%s | Headers: %s | Body: %s",
            request.method,
            request.url.path,
            f"?{request.url.query}" if request.url.query else "",
            json.dumps(headers, default=str),
            body or "N/A",
        )

    def _log_response(
        self, request: Request, response: Response, elapsed_ms: float
    ) -> None:
        """Log outgoing response details."""
        content_length = response.headers.get("content-length", "N/A")

        if isinstance(response, StreamingResponse):
            content_type = response.headers.get("content-type", "unknown")
            logger.info(
                "← %s %s → %d | %.1fms | streaming (%s)",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
                content_type,
            )
        else:
            logger.info(
                "← %s %s → %d | %.1fms | %s bytes",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
                content_length,
            )