"""
Response Compression Middleware
Adds Gzip compression to API responses for reduced bandwidth usage.
"""

import gzip
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp


class GzipMiddleware(BaseHTTPMiddleware):
    """
    Gzip middleware that compresses response bodies for text-based content types.

    Minimum size threshold of 500 bytes to avoid compressing already-small responses.
    Excludes binary content types (images, videos, etc.).
    """

    def __init__(self, app: ASGIApp, minimum_size: int = 500):
        super().__init__(app)
        self.minimum_size = minimum_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Skip compression if:
        # 1. Client doesn't accept gzip
        # 2. Response is already compressed
        # 3. Response is too small
        # 4. Content type is binary
        accept_encoding = request.headers.get("Accept-Encoding", "")
        if "gzip" not in accept_encoding:
            return response

        if response.headers.get("Content-Encoding"):
            return response

        # Check content type
        content_type = response.headers.get("Content-Type", "")
        binary_types = [
            "image/",
            "video/",
            "audio/",
            "font/",
            "application/octet-stream",
            "application/pdf",
            "application/zip",
            "application/gzip",
        ]
        if any(bt in content_type for bt in binary_types):
            return response

        try:
            body = response.body
        except Exception:
            return response

        if not body or len(body) < self.minimum_size:
            return response

        compressed = gzip.compress(body)
        if len(compressed) >= len(body):
            return response

        response.body = compressed
        response.headers["Content-Encoding"] = "gzip"
        response.headers["Content-Length"] = str(len(compressed))
        response.headers["Vary"] = "Accept-Encoding"
        return response

    async def _compress_streaming(
        self, request: Request, response: StreamingResponse
    ) -> StreamingResponse:
        """Compress a streaming response by collecting and re-streaming."""
        chunks = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                chunks.append(chunk.encode())
            else:
                chunks.append(chunk)

        body = b"".join(chunks)
        if len(body) < self.minimum_size:
            return StreamingResponse(iter(chunks), headers=response.headers)

        compressed = gzip.compress(body)
        if len(compressed) >= len(body):
            return StreamingResponse(iter(chunks), headers=response.headers)

        new_headers = dict(response.headers)
        new_headers["Content-Encoding"] = "gzip"
        new_headers["Content-Length"] = str(len(compressed))
        new_headers["Vary"] = "Accept-Encoding"

        return StreamingResponse(iter([compressed]), headers=new_headers)
