from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pytest import LogCaptureFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from education_erp.persistence.models import AuditEvent
from tests.phase2_helpers import ISSUER, auth, create_tenant, phase2_app


def test_phase3_hides_cross_tenant_learner_and_never_lists_identifier() -> None:
    with TestClient(phase2_app()) as client:
        tenant_a = create_tenant(client, slug="phase3-sec-a", owner_subject="owner-a")
        tenant_b = create_tenant(client, slug="phase3-sec-b", owner_subject="owner-b")
        created = client.post(
            f"/api/v1/tenants/{tenant_a['id']}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": "GEN-SECRET-1007"},
        )
        assert created.status_code == 201

        hidden = client.get(
            f"/api/v1/tenants/{tenant_b['id']}/learners/{created.json()['id']}",
            headers=auth("owner-b"),
        )
        assert hidden.status_code == 404

        listed = client.get(
            f"/api/v1/tenants/{tenant_a['id']}/learners",
            headers=auth("owner-a"),
        )
        rendered = listed.text
        assert "GEN-SECRET" not in rendered
        assert "1007" in rendered


def test_phase3_processing_restriction_blocks_new_enrolment() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="phase3-restrict", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        learner = client.post(
            f"/api/v1/tenants/{tenant_id}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": "GEN-RESTRICT-1"},
        )
        restricted = client.post(
            f"/api/v1/tenants/{tenant_id}/learners/{learner.json()['id']}/restrict-processing",
            headers={**auth("owner-a"), "If-Match": 'W/"1"'},
            json={"reason": "verified generated restriction request"},
        )
        assert restricted.status_code == 200

        denied = client.post(
            f"/api/v1/tenants/{tenant_id}/offering-enrolments",
            headers=auth("owner-a"),
            json={
                "learner_id": learner.json()["id"],
                "target_id": "00000000-0000-4000-8000-000000000001",
                "effective_from": "2026-01-01",
            },
        )
        assert denied.status_code == 423
        resumed = client.post(
            f"/api/v1/tenants/{tenant_id}/learners/{learner.json()['id']}/resume-processing",
            headers={**auth("owner-a"), "If-Match": 'W/"2"'},
            json={"reason": "verified generated resumption request"},
        )
        assert resumed.status_code == 200
        updated = client.patch(
            f"/api/v1/tenants/{tenant_id}/learners/{learner.json()['id']}",
            headers={**auth("owner-a"), "If-Match": 'W/"3"'},
            json={"institution_reference": "GEN-RESTRICT-2"},
        )
        assert updated.status_code == 200


def test_platform_admin_has_no_implicit_learner_access_and_reveal_requires_mfa() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="phase3-platform", owner_subject="owner-a")
        learner = client.post(
            f"/api/v1/tenants/{tenant['id']}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": "GEN-PROTECTED-1"},
        ).json()
        assert (
            client.get(
                f"/api/v1/tenants/{tenant['id']}/learners/{learner['id']}",
                headers=auth("admin"),
            ).status_code
            == 404
        )
        denied = client.post(
            f"/api/v1/tenants/{tenant['id']}/learners/{learner['id']}/reveal-reference",
            headers=auth("owner-a-without-mfa"),
            json={"reason": "verified generated identifier access"},
        )
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "mfa_required"


def test_sensitive_reason_is_persisted_in_audit() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="phase3-reason", owner_subject="owner-a")
        learner = client.post(
            f"/api/v1/tenants/{tenant['id']}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": "GEN-REASON-1"},
        ).json()
        reason = "verified generated identifier access"
        response = client.post(
            f"/api/v1/tenants/{tenant['id']}/learners/{learner['id']}/reveal-reference",
            headers=auth("owner-a"),
            json={"reason": reason},
        )
        assert response.status_code == 200
        with Session(client.app.state.database_engine) as session:
            event = session.scalar(
                select(AuditEvent).where(AuditEvent.action == "learner.reference_revealed")
            )
            assert event is not None
            assert event.reason == reason


def test_audit_outage_fails_sensitive_operation_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="phase3-audit-fail", owner_subject="owner-a")
        learner = client.post(
            f"/api/v1/tenants/{tenant['id']}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": "GEN-AUDIT-FAIL-1"},
        ).json()

        def unavailable(*args: object, **kwargs: object) -> None:
            raise RuntimeError("generated audit outage")

        monkeypatch.setattr("education_erp.api.phase3.audit", unavailable)
        with pytest.raises(RuntimeError, match="audit outage"):
            client.post(
                f"/api/v1/tenants/{tenant['id']}/learners/{learner['id']}/reveal-reference",
                headers=auth("owner-a"),
                json={"reason": "verified generated audit failure"},
            )


def test_phase3_exposes_no_physical_delete_operation() -> None:
    with TestClient(phase2_app()) as client:
        schema = client.get("/openapi.json").json()
        phase3_markers = (
            "learners",
            "enrolments",
            "academic-periods",
            "courses",
            "programmes",
            "offerings",
            "subject-rights",
            "reconciliation",
        )
        for path, operations in schema["paths"].items():
            if any(marker in path for marker in phase3_markers):
                assert "delete" not in operations


def test_phase3_idempotency_replay_is_actor_scoped() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="phase3-replay-actor", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        invited = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships",
            headers=auth("owner-a"),
            json={
                "issuer": ISSUER,
                "subject": "owner-b",
                "work_email": "generated-owner-b@example.test",
                "display_name": "Generated Owner B",
            },
        ).json()
        assigned = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{invited['id']}/role-assignments",
            headers=auth("owner-a"),
            json={"role": "registrar"},
        )
        assert assigned.status_code == 201
        shared_key = "generated-shared-replay-key"
        first = client.post(
            f"/api/v1/tenants/{tenant_id}/learners",
            headers={
                **auth("owner-a"),
                "Idempotency-Key": shared_key,
            },
            json={"institution_reference": "GEN-ACTOR-A"},
        )
        second = client.post(
            f"/api/v1/tenants/{tenant_id}/learners",
            headers={
                **auth("owner-b"),
                "Idempotency-Key": shared_key,
            },
            json={"institution_reference": "GEN-ACTOR-B"},
        )
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["id"] != second.json()["id"]


def test_learner_identifier_never_enters_request_telemetry(
    caplog: LogCaptureFixture,
) -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="phase3-telemetry", owner_subject="owner-a")
        learner_reference = "GEN-TELEMETRY-MUST-NOT-LEAK"
        created = client.post(
            f"/api/v1/tenants/{tenant['id']}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": learner_reference},
        )
        assert created.status_code == 201
        assert learner_reference not in caplog.text


def test_export_retention_operational_verification_is_present() -> None:
    verification = (
        Path(__file__).parents[2] / "docs" / "security" / "PHASE_3_EXPORT_RETENTION_VERIFICATION.md"
    ).read_text(encoding="utf-8")
    assert "metadata-only scope" in verification
    assert "creates no downloadable subject-data artifact" in verification
    assert "24-hour expiry" in verification


def test_subject_export_requires_mfa_reason_and_single_request_scope() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="phase3-export-controls", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        learner = client.post(
            f"/api/v1/tenants/{tenant_id}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": "GEN-EXPORT-1"},
        ).json()
        subject_request = client.post(
            f"/api/v1/tenants/{tenant_id}/subject-rights-requests",
            headers=auth("owner-a"),
            json={
                "learner_id": learner["id"],
                "request_type": "access",
                "due_at": "2026-08-01T00:00:00Z",
                "reason_code": "verified_request",
            },
        ).json()
        endpoint = (
            f"/api/v1/tenants/{tenant_id}/subject-rights-requests/"
            f"{subject_request['id']}/export-manifest"
        )
        assert (
            client.post(
                endpoint,
                headers=auth("owner-a-without-mfa"),
                json={"reason": "verified generated export request"},
            ).status_code
            == 403
        )
        assert client.post(endpoint, headers=auth("owner-a"), json={}).status_code == 422
        created = client.post(
            endpoint,
            headers=auth("owner-a"),
            json={"reason": "verified generated export request"},
        )
        assert created.status_code == 201
        assert created.json()["learner_id"] == learner["id"]
        assert (
            client.post(
                endpoint,
                headers=auth("owner-a"),
                json={"reason": "verified generated repeated export request"},
            ).status_code
            == 409
        )
