"""
Prometheus Metrics Middleware
Exposes application metrics for Prometheus scraping.
"""
import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp

logger = logging.getLogger("api.metrics")


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects Prometheus-compatible metrics from HTTP requests.

    Metrics collected:
    - http_requests_total (counter)
    - http_request_duration_seconds (histogram)
    - http_requests_in_progress (gauge)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._request_counts: dict[str, int] = defaultdict(int)
        self._request_durations: dict[str, list[float]] = defaultdict(list)
        self._active_requests: int = 0
        self._total_requests: int = 0
        self._total_errors: int = 0

    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        path = self._normalize_path(request.url.path)
        key = f"{method} {path}"

        self._active_requests += 1
        self._total_requests += 1
        start_time = time.perf_counter()

        try:
            response: Response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            self._total_errors += 1
            raise
        finally:
            elapsed = time.perf_counter() - start_time
            self._active_requests -= 1

            # Record metrics
            self._request_counts[key] += 1
            self._request_durations[key].append(elapsed)

            # Keep only last 1000 durations to prevent memory growth
            if len(self._request_durations[key]) > 1000:
                self._request_durations[key] = self._request_durations[key][-1000:]

        # Add metrics headers
        response.headers["X-Metrics-Request-Count"] = str(self._request_counts[key])
        return response

    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing UUIDs and IDs with placeholders."""
        import re
        # Replace UUIDs
        path = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "{id}", path)
        # Replace numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)
        return path

    def get_metrics(self) -> str:
        """
        Return Prometheus-formatted metrics.

        Usage: expose at /metrics endpoint in your app.
        """
        lines = [
            "# HELP http_requests_total Total number of HTTP requests",
            "# TYPE http_requests_total counter",
        ]

        for route, count in sorted(self._request_counts.items()):
            safe_route = route.replace(" ", "_").replace("/", "_").strip("_")
            lines.append(f'http_requests_total{{method="{route}"}} {count}')

        lines.append("")
        lines.append("# HELP http_request_duration_seconds HTTP request duration in seconds")
        lines.append("# TYPE http_request_duration_seconds histogram")

        for route, durations in sorted(self._request_durations.items()):
            if not durations:
                continue
            safe_route = route.replace(" ", "_").replace("/", "_").strip("_")
            for d in durations:
                lines.append(f'http_request_duration_seconds{{method="{route}"}} {d:.6f}')

        lines.append("")
        lines.append("# HELP http_requests_in_progress Current number of in-progress requests")
        lines.append("# TYPE http_requests_in_progress gauge")
        lines.append(f"http_requests_in_progress {self._active_requests}")

        lines.append("")
        lines.append("# HELP http_requests_total_all Total HTTP requests across all routes")
        lines.append("# TYPE http_requests_total_all counter")
        lines.append(f"http_requests_total_all {self._total_requests}")

        lines.append("")
        lines.append("# HELP http_errors_total Total HTTP errors")
        lines.append("# TYPE http_errors_total counter")
        lines.append(f"http_errors_total {self._total_errors}")

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """Get human-readable stats summary."""
        stats = {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "active_requests": self._active_requests,
            "routes": {},
        }

        for route in self._request_counts:
            durations = self._request_durations.get(route, [])
            count = self._request_counts[route]
            stats["routes"][route] = {
                "count": count,
                "avg_ms": round((sum(durations) / len(durations)) * 1000, 2) if durations else 0,
                "max_ms": round(max(durations) * 1000, 2) if durations else 0,
                "p95_ms": round(sorted(durations)[int(len(durations) * 0.95)] * 1000, 2) if len(durations) > 1 else 0,
            }

        return stats