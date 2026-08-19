from datetime import timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from education_erp.connectors.service import (
    execute_job,
    purge_expired_staging,
    replay_dead_letter_record,
    run_job_durably,
)
from education_erp.persistence.connector_models import (
    Connector,
    ConnectorBatch,
    DeadLetter,
    MappingVersion,
    StagingRecord,
    SyncJob,
)
from education_erp.persistence.models import User
from tests.phase2_helpers import auth, create_tenant, phase2_app


def test_rolled_back_worker_batch_resumes_without_duplicate_or_skip() -> None:
    from fastapi.testclient import TestClient

    app = phase2_app()
    client = TestClient(app)
    tenant = create_tenant(client, slug="connector-resume", owner_subject="owner-a")
    tenant_id = str(tenant["id"])
    created = client.post(
        f"/api/v1/tenants/{tenant_id}/connectors",
        headers=auth("owner-a"),
        json={"name": "Generated resume", "kind": "generated_mock_v1", "scenario": "valid"},
    )
    assert created.status_code == 201
    with Session(app.state.database_engine) as session:
        connector = session.scalar(select(Connector).where(Connector.tenant_id == tenant_id))
        mapping = session.scalar(
            select(MappingVersion).where(MappingVersion.tenant_id == tenant_id)
        )
        user = session.scalar(select(User).where(User.work_email == "owner-a@example.test"))
        assert connector and mapping and user
        job = SyncJob(
            tenant_id=tenant_id,
            connector_id=connector.id,
            mapping_version_id=mapping.id,
            scenario="valid",
            requested_by_user_id=user.id,
        )
        session.add(job)
        session.flush()
        job_id = job.id
        execute_job(session, tenant_id=tenant_id, job_id=job_id, worker_id="killed-worker")
        assert session.scalar(select(func.count(StagingRecord.id))) == 9
        session.rollback()
    with Session(app.state.database_engine) as session, session.begin():
        session.execute(text("SELECT 1"))
        connector = session.scalar(select(Connector).where(Connector.tenant_id == tenant_id))
        mapping = session.scalar(
            select(MappingVersion).where(MappingVersion.tenant_id == tenant_id)
        )
        user = session.scalar(select(User).where(User.work_email == "owner-a@example.test"))
        assert connector and mapping and user
        replacement = SyncJob(
            tenant_id=tenant_id,
            connector_id=connector.id,
            mapping_version_id=mapping.id,
            scenario="valid",
            requested_by_user_id=user.id,
        )
        session.add(replacement)
        session.flush()
        result = execute_job(
            session, tenant_id=tenant_id, job_id=replacement.id, worker_id="replacement-worker"
        )
        assert result.state == "succeeded"
        assert result.accepted_count == 9
        assert result.duplicate_count == 0
        assert session.scalar(select(func.count(StagingRecord.id))) == 9
    client.close()


def test_durable_batches_replay_and_expiry_cleanup() -> None:
    from fastapi.testclient import TestClient

    from education_erp.persistence.models import utc_now

    app = phase2_app()
    client = TestClient(app)
    tenant = create_tenant(client, slug="connector-durable", owner_subject="owner-a")
    tenant_id = str(tenant["id"])
    response = client.post(
        f"/api/v1/tenants/{tenant_id}/connectors",
        headers=auth("owner-a"),
        json={"name": "Generated durable", "kind": "generated_mock_v1", "scenario": "valid"},
    )
    assert response.status_code == 201
    with Session(app.state.database_engine) as session, session.begin():
        connector = session.scalar(select(Connector).where(Connector.tenant_id == tenant_id))
        mapping = session.scalar(
            select(MappingVersion).where(MappingVersion.tenant_id == tenant_id)
        )
        user = session.scalar(select(User).where(User.work_email == "owner-a@example.test"))
        assert connector and mapping and user
        job = SyncJob(
            tenant_id=tenant_id,
            connector_id=connector.id,
            mapping_version_id=mapping.id,
            scenario="valid",
            requested_by_user_id=user.id,
        )
        session.add(job)
        session.flush()
        job_id = job.id
    with Session(app.state.database_engine) as session, session.begin():
        interrupted = execute_job(
            session,
            tenant_id=tenant_id,
            job_id=job_id,
            worker_id="terminated-worker",
            batch_size=5,
            max_batches=1,
        )
        assert interrupted.state == "running"
        assert interrupted.accepted_count == 5
    result = run_job_durably(
        app.state.database_engine,
        tenant_id=tenant_id,
        job_id=job_id,
        worker_id="durable-worker",
        batch_size=5,
    )
    assert result.state == "succeeded"
    with (
        Session(app.state.database_engine) as session,
        session.begin(),
        pytest.raises(LookupError),
    ):
        execute_job(session, tenant_id="", job_id=job_id, worker_id="tenantless-worker")
    with Session(app.state.database_engine) as session, session.begin():
        assert (
            session.scalar(
                select(func.count())
                .select_from(StagingRecord)
                .where(StagingRecord.tenant_id == tenant_id)
            )
            == 9
        )
        assert (
            session.scalar(
                select(func.count())
                .select_from(ConnectorBatch)
                .where(
                    ConnectorBatch.tenant_id == tenant_id,
                    ConnectorBatch.job_id == job_id,
                )
            )
            == 2
        )
        staging = session.scalar(
            select(StagingRecord)
            .where(StagingRecord.tenant_id == tenant_id)
            .order_by(StagingRecord.created_at)
        )
        assert staging is not None
        staging.outcome = "dead_letter"
        dead_letter = DeadLetter(
            tenant_id=tenant_id,
            staging_record_id=staging.id,
            failure_code="generated_test_failure",
        )
        session.add(dead_letter)
        session.flush()
        replayed = replay_dead_letter_record(
            session, tenant_id=tenant_id, dead_letter_id=dead_letter.id
        )
        assert replayed.replay_state == "resolved"
        staging.expires_at = utc_now() - timedelta(seconds=1)
    with Session(app.state.database_engine) as session, session.begin():
        assert purge_expired_staging(session, tenant_id=tenant_id) == 1
        assert purge_expired_staging(session, tenant_id=tenant_id) == 0
    client.close()
