"""Rate limit in-memory por IP (MVP local)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import Settings, get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings | None = None) -> None:
        super().__init__(app)
        self.settings = settings or get_settings()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/v1/consultations"):
            return await call_next(request)

        now = time.monotonic()
        window = 60.0
        limit = self.settings.rate_limit_per_minute
        key = self._client_key(request)
        bucket = self._hits[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Demasiadas consultas. Intentá de nuevo en un minuto.",
                    "code": "rate_limit_exceeded",
                },
            )
        bucket.append(now)
        return await call_next(request)
