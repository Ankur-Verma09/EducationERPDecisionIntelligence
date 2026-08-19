import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from education_erp.events import EventEnvelope, enqueue_event, record_processed_event
from education_erp.persistence.event_models import OutboxEvent, ProcessedEvent

pytestmark = pytest.mark.integration


def test_postgresql_outbox_and_processed_event_foundations() -> None:
    database_url = os.getenv("EDUERP_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("EDUERP_TEST_DATABASE_URL is required for PostgreSQL integration")
    engine = create_engine(database_url)
    envelope = EventEnvelope(
        event_type="foundation.contract_verified",
        aggregate_id=uuid4(),
        tenant_id=uuid4(),
        trace_id=uuid4(),
        payload={"contains_personal_data": False},
    )
    with Session(engine) as session:
        session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(envelope.tenant_id)},
        )
        outbox = enqueue_event(session, envelope)
        assert record_processed_event(
            session,
            consumer_name="foundation-test-v1",
            event_id=envelope.event_id,
            tenant_id=envelope.tenant_id,
        )
        outbox_id = outbox.id
        session.commit()

    with Session(engine) as session:
        session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(envelope.tenant_id)},
        )
        assert session.get(OutboxEvent, outbox_id) is not None
        processed = session.scalar(
            select(ProcessedEvent).where(
                ProcessedEvent.consumer_name == "foundation-test-v1",
                ProcessedEvent.event_id == str(envelope.event_id),
            )
        )
        assert processed is not None
