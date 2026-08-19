"""Credential-free internal test double for the future AI deployment boundary."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from education_erp.ai_contracts import AiServiceHealth, AiUnavailable

app = FastAPI(title="Internal AI Contract Test Double", docs_url=None, redoc_url=None)


@app.get("/health/live", response_model=AiServiceHealth)
def live() -> AiServiceHealth:
    return AiServiceHealth(status="ok")


@app.get("/health/ready", response_model=AiServiceHealth)
def ready() -> AiServiceHealth:
    return AiServiceHealth(status="degraded")


@app.post("/internal/v1/generate", response_model=AiUnavailable, status_code=503)
def generate_unavailable() -> JSONResponse:
    return JSONResponse(status_code=503, content=AiUnavailable().model_dump())
