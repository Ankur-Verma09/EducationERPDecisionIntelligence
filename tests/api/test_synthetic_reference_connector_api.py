from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from education_erp.persistence.connector_models import (
    Connector,
    ReconciliationRun,
    SourceSchema,
    StagingRecord,
    TransportConfig,
)
from education_erp.persistence.event_models import OutboxEvent
from education_erp.persistence.phase3_models import OfferingEnrolment, ProgrammeEnrolment
from tests.phase2_helpers import auth, create_tenant, phase2_app


def _create(client: TestClient, tenant_id: str, scenario: str = "valid") -> dict[str, object]:
    response = client.post(
        f"/api/v1/tenants/{tenant_id}/connectors",
        headers=auth("owner-a"),
        json={
            "name": "Synthetic Reference Demo",
            "kind": "synthetic_reference_erp_v1",
            "package_version": "1.0.0",
            "scenario": scenario,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_demo_connector_verifies_package_and_runs_generated_records() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="synthetic-reference", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _create(client, tenant_id)
        tested = client.post(
            f"/api/v1/tenants/{tenant_id}/connectors/{connector['id']}/test",
            headers=auth("owner-a"),
        )
        assert tested.status_code == 200
        assert tested.json() == {
            "connector_id": connector["id"],
            "status": "ok",
            "contract_version": "1",
            "sample_count": 1,
            "package_version": "1.0.0",
            "network_egress": False,
            "credential_reference": None,
        }
        sync = client.post(
            f"/api/v1/tenants/{tenant_id}/sync-jobs",
            headers=auth("owner-a"),
            json={
                "connector_id": connector["id"],
                "test_clock": "2030-01-16T00:01:00Z",
            },
        )
        assert sync.status_code == 201, sync.text
        assert sync.json()["state"] == "succeeded"
        assert sync.json()["accepted_count"] == 12
        with Session(app.state.database_engine) as session:
            assert session.scalar(select(func.count(SourceSchema.id))) == 1
            transport = session.scalar(select(TransportConfig))
            assert transport is not None
            assert transport.network_egress is False
            assert transport.credential_reference is None
            run = session.scalar(select(ReconciliationRun))
            assert run is not None
            assert run.disposition == "matched"
            assert run.breach_codes == []
            assert run.threshold_snapshot["version"] == "1"
            event_types = set(session.scalars(select(OutboxEvent.event_type)))
            assert event_types == {
                "connector.package_verified.v1",
                "connector.sync_started.v1",
                "connector.batch_validated.v1",
                "connector.sync_completed.v1",
            }
            assert all(session.scalars(select(OutboxEvent.correlation_id)))
            assert session.scalar(select(ProgrammeEnrolment.status)) == "active"
            assert session.scalar(select(OfferingEnrolment.status)) == "active"


def test_demo_api_rejects_network_credentials_paths_tls_and_wrong_version() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="synthetic-closed", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        base = {
            "name": "Unsafe",
            "kind": "synthetic_reference_erp_v1",
            "package_version": "1.0.0",
            "scenario": "valid",
        }
        for extra in (
            {"url": "https://example.test"},
            {"path": "C:/customer.csv"},
            {"host": "erp.internal"},
            {"credential": "secret"},
            {"tls_verify": False},
        ):
            response = client.post(
                f"/api/v1/tenants/{tenant_id}/connectors",
                headers=auth("owner-a"),
                json={**base, **extra},
            )
            assert response.status_code == 422
        wrong = client.post(
            f"/api/v1/tenants/{tenant_id}/connectors",
            headers=auth("owner-a"),
            json={**base, "package_version": "2.0.0"},
        )
        assert wrong.status_code == 422


def test_demo_quarantine_threshold_block_and_no_sensitive_persistence() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="synthetic-quarantine", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _create(client, tenant_id, "prohibited-child-attribute")
        sync = client.post(
            f"/api/v1/tenants/{tenant_id}/sync-jobs",
            headers=auth("owner-a"),
            json={"connector_id": connector["id"]},
        )
        assert sync.status_code == 201
        assert sync.json()["state"] == "failed"
        with Session(app.state.database_engine) as session:
            run = session.scalar(select(ReconciliationRun))
            assert run is not None
            assert run.disposition == "blocked"
            assert "reconciliation_threshold_breached" in run.breach_codes
            quarantined = session.scalar(
                select(StagingRecord).where(StagingRecord.outcome == "quarantined")
            )
            assert quarantined is not None
            assert quarantined.normalized_document is None
            serialized_events = str(list(session.scalars(select(OutboxEvent.payload))))
            assert "health_note" not in serialized_events
            assert "generated-prohibited" not in serialized_events
            stored = session.scalar(select(Connector))
            assert stored is not None
            assert "credential" not in str(stored.config)
