from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from education_erp.persistence.connector_models import ReconciliationRun, StagingRecord, SyncJob
from education_erp.persistence.event_models import OutboxEvent
from education_erp.persistence.phase3_models import AcademicPeriod, Learner, ReconciliationIssue
from tests.phase2_helpers import auth, create_tenant, phase2_app


def _connector(client: TestClient, tenant_id: str, scenario: str) -> dict[str, object]:
    response = client.post(
        f"/api/v1/tenants/{tenant_id}/connectors",
        headers=auth("owner-a"),
        json={
            "name": f"Synthetic {scenario}",
            "kind": "synthetic_reference_erp_v1",
            "package_version": "1.0.0",
            "scenario": scenario,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _sync(client: TestClient, tenant_id: str, connector_id: object, **extra: object):
    return client.post(
        f"/api/v1/tenants/{tenant_id}/sync-jobs",
        headers=auth("owner-a"),
        json={"connector_id": connector_id, **extra},
    )


def test_schema_drift_transport_failures_and_core_health_are_isolated() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="synthetic-outage", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        for scenario, expected in (
            ("schema-drift-extra-field", "source_schema_unsupported"),
            ("transport-timeout", "transport_unavailable"),
            ("transport-throttled", "transport_unavailable"),
            ("credential-rejected", "invalid_connector_config"),
        ):
            connector = _connector(client, tenant_id, scenario)
            tested = client.post(
                f"/api/v1/tenants/{tenant_id}/connectors/{connector['id']}/test",
                headers=auth("owner-a"),
            )
            assert tested.status_code in {409, 422, 503}
            assert tested.json()["error"]["code"] == expected
            synced = _sync(client, tenant_id, connector["id"])
            assert synced.status_code == 201
            assert synced.json()["state"] == "failed"
            assert synced.json()["failure_code"] == expected
            assert synced.json()["attempt"] == (3 if expected == "transport_unavailable" else 1)
            assert client.get("/api/v1/health/live").json()["status"] == "ok"
        with Session(client.app.state.database_engine) as session:
            assert session.scalar(select(func.count(SyncJob.id))) == 4
            event_types = set(session.scalars(select(OutboxEvent.event_type)))
            assert "connector.sync_failed.v1" in event_types
            assert "connector.schema_drift_detected.v1" in event_types


def test_identity_ambiguity_does_not_auto_merge_or_expose_source_keys() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="synthetic-identity", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _connector(client, tenant_id, "ambiguous-identity")
        response = _sync(client, tenant_id, connector["id"])
        assert response.status_code == 201
        with Session(app.state.database_engine) as session:
            assert session.scalar(select(func.count(Learner.id))) == 2
            issues = list(
                session.scalars(
                    select(ReconciliationIssue).where(ReconciliationIssue.tenant_id == tenant_id)
                )
            )
            assert issues
        assert "L-9999" not in response.text
        assert "SYN-0001" not in response.text


def test_late_correction_cannot_overwrite_current_projection() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="synthetic-late", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _connector(client, tenant_id, "late-correction")
        response = _sync(client, tenant_id, connector["id"])
        assert response.status_code == 201
        with Session(app.state.database_engine) as session:
            period = session.scalar(
                select(AcademicPeriod).where(AcademicPeriod.tenant_id == tenant_id)
            )
            assert period is not None
            assert period.name == "Generated Academic Year 2030"
            assert session.scalar(select(func.count(ReconciliationIssue.id))) >= 1


def test_thresholds_are_immutable_snapshots_and_block_duplicate_promotion() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="synthetic-threshold", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _connector(client, tenant_id, "duplicate-version")
        response = _sync(client, tenant_id, connector["id"])
        assert response.status_code == 201
        assert response.json()["state"] == "failed"
        with Session(app.state.database_engine) as session:
            run = session.scalar(select(ReconciliationRun))
            assert run is not None
            assert run.threshold_snapshot["duplicate_max_percent"] == 2.0
            assert run.disposition == "blocked"
            assert run.breach_codes == ["reconciliation_threshold_breached"]


def test_stale_test_clock_blocks_freshness_and_staging_is_bounded() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="synthetic-freshness", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _connector(client, tenant_id, "valid")
        response = _sync(
            client,
            tenant_id,
            connector["id"],
            test_clock="2030-01-16T02:30:00Z",
        )
        assert response.status_code == 201
        assert response.json()["state"] == "failed"
        with Session(app.state.database_engine) as session:
            run = session.scalar(select(ReconciliationRun))
            assert run is not None
            assert "freshness_threshold_breached" in run.breach_codes
            rows = list(session.scalars(select(StagingRecord)))
            assert rows
            now = datetime.now(UTC)
            assert all(
                row.expires_at.replace(tzinfo=UTC) <= now + timedelta(hours=24, minutes=1)
                for row in rows
            )
