"""Liveness and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import Engine

from education_erp.database import database_is_ready

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "not_ready"]


@router.get("/live", response_model=HealthResponse, summary="Process liveness")
def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "Dependency unavailable"}},
    summary="Service readiness",
)
def readiness(request: Request, response: Response) -> HealthResponse:
    engine: Engine = request.app.state.database_engine
    if not database_is_ready(engine):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="not_ready")
    return HealthResponse(status="ok")
