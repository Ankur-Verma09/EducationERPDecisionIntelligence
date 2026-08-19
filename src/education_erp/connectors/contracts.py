"""Closed connector adapter and generated record contracts."""

from datetime import datetime
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

APPROVED_ENTITY_TYPES = frozenset(
    {
        "academic-period",
        "programme",
        "programme-version",
        "course",
        "course-version",
        "offering",
        "learner",
        "programme-enrolment",
        "offering-enrolment",
    }
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdapterRecord(StrictModel):
    entity_type: Literal[
        "academic-period",
        "programme",
        "programme-version",
        "course",
        "course-version",
        "offering",
        "learner",
        "programme-enrolment",
        "offering-enrolment",
    ]
    source_record_key: str = Field(min_length=1, max_length=200)
    source_record_version: str = Field(min_length=1, max_length=64)
    observed_at: datetime
    effective_at: datetime
    document: dict[str, Any]


class AdapterBatch(StrictModel):
    records: tuple[AdapterRecord, ...]
    next_checkpoint: str = Field(max_length=120)
    source_exhausted: bool
    expected_total: int = Field(ge=0, le=10_000)
    expected_rejections: int = Field(ge=0, le=10_000)
    expected_duplicates: int = Field(ge=0, le=10_000)


class ConnectorAdapter(Protocol):
    def read_batch(self, checkpoint: str, limit: int) -> AdapterBatch: ...
