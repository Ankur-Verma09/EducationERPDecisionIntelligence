from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from education_erp.events import EventEnvelope, enqueue_event, record_processed_event
from education_erp.persistence.base import Base
from education_erp.persistence.event_models import OutboxEvent, ProcessedEvent


def test_event_envelope_is_versioned_and_forbids_unknown_fields() -> None:
    envelope = EventEnvelope(
        event_type="learner.updated",
        aggregate_id=uuid4(),
        tenant_id=uuid4(),
        trace_id=uuid4(),
        payload={"changed_fields": ["status"]},
    )
    assert envelope.schema_version == "1"

    with pytest.raises(ValidationError):
        EventEnvelope(
            event_type="learner.updated",
            aggregate_id=uuid4(),
            tenant_id=uuid4(),
            trace_id=uuid4(),
            payload={},
            source_database="forbidden",
        )


def test_outbox_commit_is_atomic_with_domain_transaction() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    envelope = EventEnvelope(
        event_type="learner.updated",
        aggregate_id=uuid4(),
        tenant_id=uuid4(),
        trace_id=uuid4(),
        payload={"minimum": "necessary"},
    )

    with Session(engine) as session:
        enqueue_event(session, envelope)
        session.rollback()
    with Session(engine) as session:
        assert session.scalar(select(OutboxEvent)) is None

    with Session(engine) as session:
        enqueue_event(session, envelope)
        session.commit()
    with Session(engine) as session:
        stored = session.scalar(select(OutboxEvent))
        assert stored is not None
        assert stored.event_id == str(envelope.event_id)
        assert stored.payload == {"minimum": "necessary"}


def test_processed_event_is_idempotent_per_consumer() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    event_id = uuid4()
    tenant_id = uuid4()

    with Session(engine) as session:
        assert record_processed_event(
            session, consumer_name="reporting-v1", event_id=event_id, tenant_id=tenant_id
        )
        session.commit()
        assert not record_processed_event(
            session, consumer_name="reporting-v1", event_id=event_id, tenant_id=tenant_id
        )
        assert record_processed_event(
            session, consumer_name="audit-v1", event_id=event_id, tenant_id=tenant_id
        )
        session.commit()

    with Session(engine) as session:
        assert len(session.scalars(select(ProcessedEvent)).all()) == 2
