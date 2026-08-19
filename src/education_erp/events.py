"""Provider-neutral domain-event contracts and transactional persistence helpers."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from education_erp.persistence.event_models import OutboxEvent, ProcessedEvent


class EventEnvelope(BaseModel):
    """Versioned event envelope shared without coupling to a broker implementation."""

    model_config = ConfigDict(extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,119}$")
    aggregate_id: UUID
    tenant_id: UUID
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: Literal["1"] = "1"
    trace_id: UUID
    correlation_id: UUID | None = None
    causation_id: UUID | None = None
    payload: dict[str, Any]


def enqueue_event(session: Session, envelope: EventEnvelope) -> OutboxEvent:
    """Add an event to the caller's transaction; committing remains caller-owned."""

    record = OutboxEvent(
        event_id=str(envelope.event_id),
        event_type=envelope.event_type,
        aggregate_id=str(envelope.aggregate_id),
        tenant_id=str(envelope.tenant_id),
        occurred_at=envelope.occurred_at,
        schema_version=envelope.schema_version,
        trace_id=str(envelope.trace_id),
        correlation_id=str(envelope.correlation_id) if envelope.correlation_id else None,
        causation_id=str(envelope.causation_id) if envelope.causation_id else None,
        payload=envelope.payload,
    )
    session.add(record)
    return record


def record_processed_event(
    session: Session, *, consumer_name: str, event_id: UUID, tenant_id: UUID
) -> bool:
    """Persist consumer deduplication and return false for a prior event."""

    existing = session.scalar(
        select(ProcessedEvent).where(
            ProcessedEvent.consumer_name == consumer_name,
            ProcessedEvent.event_id == str(event_id),
        )
    )
    if existing is not None:
        return False
    try:
        with session.begin_nested():
            session.add(
                ProcessedEvent(
                    consumer_name=consumer_name,
                    event_id=str(event_id),
                    tenant_id=str(tenant_id),
                )
            )
            session.flush()
    except IntegrityError:
        return False
    return True
