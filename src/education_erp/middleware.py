"""Request-scoped observability and baseline HTTP security controls."""

import logging
import time
from uuid import UUID, uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


def security_headers(request_id: str) -> dict[str, str]:
    """Return the headers required on every API response, including failures."""

    return {
        REQUEST_ID_HEADER: request_id,
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
    }


def valid_request_id(value: str | None) -> str:
    """Accept only UUID request IDs to prevent log/header injection."""

    if value:
        try:
            return str(UUID(value))
        except ValueError:
            return str(uuid4())
    return str(uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Set request ID, emit access logs, and attach secure response headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = valid_request_id(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers.update(security_headers(request_id))
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
