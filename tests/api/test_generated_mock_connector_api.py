from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from education_erp.persistence.connector_models import DeadLetter, ReconciliationRun, StagingRecord
from education_erp.persistence.event_models import OutboxEvent
from education_erp.persistence.phase3_models import (
    AcademicPeriod,
    Learner,
    ReconciliationIssue,
    SourceObservation,
)
from tests.phase2_helpers import auth, create_tenant, phase2_app


def test_worker_creates_and_replays_immutable_dead_letter(monkeypatch: object) -> None:
    from dataclasses import replace
    from datetime import timedelta

    import education_erp.connectors.service as service
    from education_erp.persistence.models import AuditEvent
    from tests.phase2_helpers import principal

    app = phase2_app()
    original_target = service._target
    calls = 0

    def fail_first(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("generated projection outage")
        return original_target(*args, **kwargs)

    monkeypatch.setattr(service, "_target", fail_first)  # type: ignore[attr-defined]
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="connector-dead-letter", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _create(client, tenant_id, "valid")
        sync = client.post(
            f"/api/v1/tenants/{tenant_id}/sync-jobs",
            headers=auth("owner-a"),
            json={"connector_id": connector["id"]},
        )
        assert sync.status_code == 201
        with Session(app.state.database_engine) as session:
            dead_letter = session.scalar(
                select(DeadLetter).where(DeadLetter.tenant_id == tenant_id)
            )
            assert dead_letter is not None
            dead_letter_id = dead_letter.id
            staging = session.get(StagingRecord, dead_letter.staging_record_id)
            assert staging is not None and staging.normalized_document is not None
            immutable_input = dict(staging.normalized_document)
        monkeypatch.setattr(service, "_target", original_target)  # type: ignore[attr-defined]
        stale = replace(
            principal("owner-a", mfa=True),
            issued_at=principal("owner-a").issued_at - timedelta(hours=1),
        )
        app.state.token_verifier.principals["stale-owner"] = stale
        denied = client.post(
            f"/api/v1/tenants/{tenant_id}/dead-letters/{dead_letter_id}/replay",
            headers=auth("stale-owner"),
            json={"reason": "generated replay validation"},
        )
        assert denied.status_code == 403
        replay = client.post(
            f"/api/v1/tenants/{tenant_id}/dead-letters/{dead_letter_id}/replay",
            headers=auth("owner-a"),
            json={"reason": "generated replay validation"},
        )
        assert replay.status_code == 200
        assert replay.json()["replay_state"] == "resolved"
        assert client.get("/api/v1/health/ready").status_code == 200
        with Session(app.state.database_engine) as session:
            replay_staging = session.scalar(
                select(StagingRecord).where(StagingRecord.id == dead_letter.staging_record_id)
            )
            assert replay_staging is not None
            assert replay_staging.normalized_document == immutable_input
            assert (
                session.scalar(
                    select(AuditEvent).where(
                        AuditEvent.tenant_id == tenant_id,
                        AuditEvent.action == "connector.replay_requested",
                    )
                )
                is not None
            )


def _create(client: TestClient, tenant_id: str, scenario: str = "mixed") -> dict[str, object]:
    response = client.post(
        f"/api/v1/tenants/{tenant_id}/connectors",
        headers=auth("owner-a"),
        json={"name": "Generated SIS", "kind": "generated_mock_v1", "scenario": scenario},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_late_connector_cannot_overwrite_current_projection() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="connector-late", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _create(client, tenant_id, "late")
        sync = client.post(
            f"/api/v1/tenants/{tenant_id}/sync-jobs",
            headers=auth("owner-a"),
            json={"connector_id": connector["id"]},
        )
        assert sync.status_code == 201
        assert sync.json()["state"] == "succeeded"
        with Session(app.state.database_engine) as session:
            period = session.scalar(
                select(AcademicPeriod).where(AcademicPeriod.tenant_id == tenant_id)
            )
            assert period is not None
            assert period.name == "Generated 2030"
            issue = session.scalar(
                select(ReconciliationIssue).where(
                    ReconciliationIssue.tenant_id == tenant_id,
                    ReconciliationIssue.entity_type == "academic-period",
                )
            )
            assert issue is not None
            assert issue.issue_type == "source_conflict"


def test_generated_connector_sync_quarantine_reconciliation_and_safe_events() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="connector-generated", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _create(client, tenant_id)
        tested = client.post(
            f"/api/v1/tenants/{tenant_id}/connectors/{connector['id']}/test",
            headers=auth("owner-a"),
        )
        assert tested.status_code == 200
        sync = client.post(
            f"/api/v1/tenants/{tenant_id}/sync-jobs",
            headers=auth("owner-a"),
            json={"connector_id": connector["id"]},
        )
        assert sync.status_code == 201, sync.text
        assert sync.json()["state"] == "succeeded"
        assert sync.json()["accepted_count"] == 9
        assert sync.json()["rejected_count"] == 1
        quarantine = client.get(
            f"/api/v1/tenants/{tenant_id}/sync-jobs/{sync.json()['id']}/quarantine",
            headers=auth("owner-a"),
        )
        assert quarantine.status_code == 200
        assert quarantine.json()["items"] == [
            {
                "id": quarantine.json()["items"][0]["id"],
                "code": "schema_validation_failed",
                "field_path": "document",
                "rule_version": "1",
            }
        ]
        with Session(app.state.database_engine) as session:
            assert len(list(session.scalars(select(Learner)))) == 1
            assert len(list(session.scalars(select(SourceObservation)))) == 9
            assert session.scalar(select(ReconciliationRun.disposition)) == "matched"
            assert (
                session.scalar(
                    select(StagingRecord.normalized_document).where(
                        StagingRecord.outcome == "quarantined"
                    )
                )
                is None
            )
            events = list(session.scalars(select(OutboxEvent)))
            assert {event.event_type for event in events} == {
                "connector.sync_started",
                "connector.batch_validated",
                "connector.sync_completed",
            }
            serialized = str([event.payload for event in events])
            assert "GEN-" not in serialized
            assert "institution_reference" not in serialized


def test_connector_contract_security_idempotency_etag_and_tenant_hiding() -> None:
    with TestClient(phase2_app()) as client:
        tenant_a = create_tenant(client, slug="connector-a", owner_subject="owner-a")
        tenant_b = create_tenant(client, slug="connector-b", owner_subject="owner-b")
        tenant_a_id, tenant_b_id = str(tenant_a["id"]), str(tenant_b["id"])
        key_headers = auth("owner-a")
        key_headers["Idempotency-Key"] = "generated-replay-key"
        payload = {"name": "Generated A", "kind": "generated_mock_v1", "scenario": "valid"}
        first = client.post(
            f"/api/v1/tenants/{tenant_a_id}/connectors", headers=key_headers, json=payload
        )
        replay = client.post(
            f"/api/v1/tenants/{tenant_a_id}/connectors", headers=key_headers, json=payload
        )
        assert first.status_code == replay.status_code == 201
        assert first.json()["id"] == replay.json()["id"]
        assert first.json()["name"] == replay.json()["name"]
        conflict = client.post(
            f"/api/v1/tenants/{tenant_a_id}/connectors",
            headers=key_headers,
            json={**payload, "name": "Changed"},
        )
        assert conflict.status_code == 409
        connector_id = str(first.json()["id"])
        hidden = client.get(
            f"/api/v1/tenants/{tenant_b_id}/connectors/{connector_id}", headers=auth("owner-b")
        )
        assert hidden.status_code == 404
        missing_match = client.patch(
            f"/api/v1/tenants/{tenant_a_id}/connectors/{connector_id}",
            headers=auth("owner-a"),
            json={"status": "disabled"},
        )
        assert missing_match.status_code == 428
        invalid = client.post(
            f"/api/v1/tenants/{tenant_a_id}/connectors",
            headers=auth("owner-a"),
            json={
                "name": "Unsafe",
                "kind": "generated_mock_v1",
                "scenario": "valid",
                "url": "https://example.test",
                "credential": "secret",
            },
        )
        assert invalid.status_code == 422


def test_connector_lists_use_bound_cursor_and_cross_route_reuse_fails() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="connector-pages", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        for number in range(2):
            response = client.post(
                f"/api/v1/tenants/{tenant_id}/connectors",
                headers=auth("owner-a"),
                json={
                    "name": f"Generated {number}",
                    "kind": "generated_mock_v1",
                    "scenario": "valid",
                },
            )
            assert response.status_code == 201
        page = client.get(
            f"/api/v1/tenants/{tenant_id}/connectors?limit=1", headers=auth("owner-a")
        )
        cursor = page.json()["next_cursor"]
        assert cursor and "." in cursor
        reused = client.get(
            f"/api/v1/tenants/{tenant_id}/connectors/{page.json()['items'][0]['id']}/runs?cursor={cursor}",
            headers=auth("owner-a"),
        )
        assert reused.status_code == 400


def test_connector_update_job_history_and_reconciliation_reads() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="connector-contract", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        connector = _create(client, tenant_id, "duplicates")
        fetched = client.get(
            f"/api/v1/tenants/{tenant_id}/connectors/{connector['id']}",
            headers=auth("owner-a"),
        )
        assert fetched.status_code == 200
        assert fetched.headers["etag"] == 'W/"1"'
        stale = client.patch(
            f"/api/v1/tenants/{tenant_id}/connectors/{connector['id']}",
            headers={**auth("owner-a"), "If-Match": 'W/"9"'},
            json={"name": "Changed"},
        )
        assert stale.status_code == 412
        updated = client.patch(
            f"/api/v1/tenants/{tenant_id}/connectors/{connector['id']}",
            headers={**auth("owner-a"), "If-Match": 'W/"1"'},
            json={"name": "Generated updated", "scenario": "late"},
        )
        assert updated.status_code == 200
        assert updated.json()["version"] == 2
        sync = client.post(
            f"/api/v1/tenants/{tenant_id}/sync-jobs",
            headers=auth("owner-a"),
            json={"connector_id": connector["id"], "scenario": "duplicates"},
        )
        assert sync.status_code == 201, sync.text
        assert sync.json()["duplicate_count"] == 1
        job = client.get(
            f"/api/v1/tenants/{tenant_id}/sync-jobs/{sync.json()['id']}",
            headers=auth("owner-a"),
        )
        assert job.status_code == 200
        runs = client.get(
            f"/api/v1/tenants/{tenant_id}/connectors/{connector['id']}/runs",
            headers=auth("owner-a"),
        )
        assert runs.status_code == 200
        assert runs.json()["items"][0]["id"] == sync.json()["id"]
        with Session(app.state.database_engine) as session:
            run_id = session.scalar(select(ReconciliationRun.id))
        reconciliation = client.get(
            f"/api/v1/tenants/{tenant_id}/reconciliation-runs/{run_id}",
            headers=auth("owner-a"),
        )
        assert reconciliation.status_code == 200
        assert reconciliation.json()["disposition"] == "matched"
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/sync-jobs/missing", headers=auth("owner-a")
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/reconciliation-runs/missing",
                headers=auth("owner-a"),
            ).status_code
            == 404
        )
