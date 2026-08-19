"""Consistent public error envelopes and handlers."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from education_erp.logging import sanitize_text
from education_erp.middleware import security_headers

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Expected public API failure with a stable error code."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_payload(
    *,
    code: str,
    message: str,
    request_id: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {"code": code, "message": message, "request_id": request_id}
    }
    if details:
        payload["error"]["details"] = details
    return payload


def install_error_handlers(app: FastAPI) -> None:
    """Install validation and fail-closed unexpected-error handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_payload(
                code="validation_error",
                message="Request validation failed",
                request_id=request.state.request_id,
                details=details,
            ),
            headers=security_headers(request.state.request_id),
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled request error: %s: %s",
            type(exc).__name__,
            sanitize_text(str(exc)),
            extra={"request_id": request.state.request_id},
        )
        return JSONResponse(
            status_code=500,
            content=error_payload(
                code="internal_error",
                message="An unexpected error occurred",
                request_id=request.state.request_id,
            ),
            headers=security_headers(request.state.request_id),
        )

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=exc.code,
                message=exc.message,
                request_id=request.state.request_id,
            ),
            headers=security_headers(request.state.request_id),
        )
