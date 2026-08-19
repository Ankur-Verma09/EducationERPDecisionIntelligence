"""Internal contracts for future self-hosted AI services.

These contracts deliberately contain no model implementation or provider SDK.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class AiServiceHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded"]
    service: Literal["ai-contract-test-double"] = "ai-contract-test-double"
    inference_enabled: bool = False


class AiUnavailable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Literal["ai_unavailable"] = "ai_unavailable"
    message: str = "Self-hosted AI is not enabled in this foundation milestone"
    retryable: bool = True
