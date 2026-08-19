from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from education_erp.persistence.phase3_models import (
    LearnerLineageLink,
    ReconciliationIssue,
    SourceAuthorityRule,
    SourceObservation,
    SourceSystem,
)
from tests.phase2_helpers import auth, create_tenant, phase2_app


def _phase3_foundation(
    client: TestClient,
) -> tuple[dict[str, object], dict[str, object]]:
    tenant = create_tenant(client, slug="phase3-generated", owner_subject="owner-a")
    tenant_id = str(tenant["id"])
    period = client.post(
        f"/api/v1/tenants/{tenant_id}/academic-periods",
        headers=auth("owner-a"),
        json={
            "code": "gen-2026-t1",
            "name": "Generated Term 1",
            "period_type": "term",
            "starts_on": "2026-06-01",
            "ends_on": "2026-09-30",
        },
    )
    assert period.status_code == 201, period.text
    course = client.post(
        f"/api/v1/tenants/{tenant_id}/courses",
        headers=auth("owner-a"),
        json={"code": "gen-cs101"},
    )
    assert course.status_code == 201, course.text
    version = client.post(
        f"/api/v1/tenants/{tenant_id}/courses/{course.json()['id']}/versions",
        headers=auth("owner-a"),
        json={
            "version_code": "2026",
            "title": "Generated Computing",
            "credit_value": 4,
            "effective_from": "2026-06-01",
        },
    )
    assert version.status_code == 201, version.text
    offering = client.post(
        f"/api/v1/tenants/{tenant_id}/offerings",
        headers=auth("owner-a"),
        json={
            "code": "gen-cs101-a",
            "academic_period_id": period.json()["id"],
            "course_version_id": version.json()["id"],
        },
    )
    assert offering.status_code == 201, offering.text
    return tenant, offering.json()


def test_phase3_canonical_api_journey_and_contract() -> None:
    with TestClient(phase2_app()) as client:
        tenant, offering = _phase3_foundation(client)
        tenant_id = str(tenant["id"])
        learner = client.post(
            f"/api/v1/tenants/{tenant_id}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": "GEN-LRN-1007"},
        )
        assert learner.status_code == 201, learner.text
        assert learner.json()["institution_reference_masked"].endswith("1007")
        assert "institution_reference" not in learner.json()

        enrolment = client.post(
            f"/api/v1/tenants/{tenant_id}/offering-enrolments",
            headers=auth("owner-a"),
            json={
                "learner_id": learner.json()["id"],
                "target_id": offering["id"],
                "effective_from": "2026-06-15",
            },
        )
        assert enrolment.status_code == 201, enrolment.text
        activated = client.post(
            f"/api/v1/tenants/{tenant_id}/offering-enrolments/{enrolment.json()['id']}/activate",
            headers={**auth("owner-a"), "If-Match": 'W/"1"'},
        )
        assert activated.status_code == 200, activated.text
        assert activated.json()["status"] == "active"

        revealed = client.post(
            f"/api/v1/tenants/{tenant_id}/learners/{learner.json()['id']}/reveal-reference",
            headers=auth("owner-a"),
            json={"reason": "verified generated subject request"},
        )
        assert revealed.status_code == 200
        assert revealed.json()["institution_reference"] == "GEN-LRN-1007"
        assert revealed.headers["cache-control"] == "no-store"

        schema = client.get("/openapi.json").json()
        learner_schema = schema["components"]["schemas"]["LearnerInput"]
        assert learner_schema["additionalProperties"] is False
        mutation = schema["paths"]["/api/v1/tenants/{tenant_id}/learners"]["post"]
        assert any(item["name"] == "Idempotency-Key" for item in mutation["parameters"])

        periods = client.get(
            f"/api/v1/tenants/{tenant_id}/academic-periods",
            headers=auth("owner-a"),
        )
        assert periods.status_code == 200
        period = periods.json()["items"][0]
        detail = client.get(
            f"/api/v1/tenants/{tenant_id}/academic-periods/{period['id']}",
            headers=auth("owner-a"),
        )
        assert detail.headers["etag"] == 'W/"1"'
        updated = client.patch(
            f"/api/v1/tenants/{tenant_id}/academic-periods/{period['id']}",
            headers={**auth("owner-a"), "If-Match": 'W/"1"'},
            json={
                "code": "GEN-2026-T1",
                "name": "Generated Term One",
                "period_type": "term",
                "starts_on": "2026-06-01",
                "ends_on": "2026-09-30",
            },
        )
        assert updated.status_code == 200
        courses = client.get(
            f"/api/v1/tenants/{tenant_id}/courses", headers=auth("owner-a")
        ).json()["items"]
        course_id = courses[0]["id"]
        course_detail = client.get(
            f"/api/v1/tenants/{tenant_id}/courses/{course_id}",
            headers=auth("owner-a"),
        )
        assert course_detail.status_code == 200
        assert (
            client.patch(
                f"/api/v1/tenants/{tenant_id}/courses/{course_id}",
                headers={**auth("owner-a"), "If-Match": 'W/"1"'},
                json={"code": "GEN-CS-101"},
            ).status_code
            == 200
        )
        offering_detail = client.get(
            f"/api/v1/tenants/{tenant_id}/offerings/{offering['id']}",
            headers=auth("owner-a"),
        )
        assert offering_detail.status_code == 200
        assert (
            client.patch(
                f"/api/v1/tenants/{tenant_id}/offerings/{offering['id']}",
                headers={**auth("owner-a"), "If-Match": 'W/"1"'},
                json={
                    "code": "GEN-CS101-B",
                    "academic_period_id": period["id"],
                    "course_version_id": offering["course_version_id"],
                },
            ).status_code
            == 200
        )
        programme = client.post(
            f"/api/v1/tenants/{tenant_id}/programmes",
            headers=auth("owner-a"),
            json={"code": "GEN-BSC-CS"},
        )
        assert programme.status_code == 201
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/programmes/{programme.json()['id']}",
                headers={
                    **auth("owner-a"),
                    "X-Access-Reason": "verified generated subject request read",
                },
            ).status_code
            == 200
        )
        assert (
            client.patch(
                f"/api/v1/tenants/{tenant_id}/programmes/{programme.json()['id']}",
                headers={**auth("owner-a"), "If-Match": 'W/"1"'},
                json={"code": "GEN-BSC-COMPUTING"},
            ).status_code
            == 200
        )
        programme_version = client.post(
            f"/api/v1/tenants/{tenant_id}/programmes/{programme.json()['id']}/versions",
            headers=auth("owner-a"),
            json={
                "version_code": "2026",
                "name": "Generated Computing Programme",
                "effective_from": "2026-06-01",
            },
        )
        assert programme_version.status_code == 201
        programme_enrolment = client.post(
            f"/api/v1/tenants/{tenant_id}/programme-enrolments",
            headers=auth("owner-a"),
            json={
                "learner_id": learner.json()["id"],
                "target_id": programme_version.json()["id"],
                "effective_from": "2026-06-15",
            },
        )
        assert programme_enrolment.status_code == 201
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/programme-enrolments/"
                f"{programme_enrolment.json()['id']}",
                headers={
                    **auth("owner-a"),
                    "X-Access-Reason": "verified generated subject request list",
                },
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/programme-enrolments",
                headers=auth("owner-a"),
            ).status_code
            == 200
        )
        with Session(client.app.state.database_engine) as session, session.begin():
            source = SourceSystem(
                tenant_id=tenant_id,
                code="GEN-SOURCE",
                display_name="Generated source",
            )
            session.add(source)
            session.flush()
            session.add(
                SourceAuthorityRule(
                    tenant_id=tenant_id,
                    source_system_id=source.id,
                    entity_type="learner",
                    authority="primary",
                    effective_from=date(2026, 1, 1),
                )
            )
            observation = SourceObservation(
                tenant_id=tenant_id,
                source_system_id=source.id,
                entity_type="learner",
                source_record_key="GEN-KEY",
                source_record_fingerprint="generated-fingerprint",
                source_record_version="v1",
                schema_version="1",
                mapping_version="map-1",
                observed_at=datetime(2026, 7, 1, tzinfo=UTC),
                effective_at=datetime(2026, 6, 1, tzinfo=UTC),
                semantic_hash="generated-hash",
            )
            session.add(observation)
            session.flush()
            session.add(
                LearnerLineageLink(
                    tenant_id=tenant_id,
                    source_observation_id=observation.id,
                    learner_id=learner.json()["id"],
                    relationship="create",
                )
            )
        lineage = client.get(
            f"/api/v1/tenants/{tenant_id}/canonical-records/learner/{learner.json()['id']}/lineage",
            headers=auth("owner-a"),
        )
        assert lineage.status_code == 200
        assert set(lineage.json()["items"][0]) == {
            "source_code",
            "observation_id",
            "source_record_version",
            "mapping_version",
            "authority",
            "observed_at",
            "effective_at",
            "recorded_at",
            "relationship",
        }
        for entity_type in (
            "academic-period",
            "programme",
            "programme-version",
            "course",
            "course-version",
            "offering",
            "programme-enrolment",
            "offering-enrolment",
        ):
            response = client.get(
                f"/api/v1/tenants/{tenant_id}/canonical-records/{entity_type}/"
                "00000000-0000-4000-8000-000000000099/lineage",
                headers=auth("owner-a"),
            )
            assert response.status_code == 404
        subject_request = client.post(
            f"/api/v1/tenants/{tenant_id}/subject-rights-requests",
            headers=auth("owner-a"),
            json={
                "learner_id": learner.json()["id"],
                "request_type": "access",
                "due_at": "2026-08-01T00:00:00Z",
                "reason_code": "verified_request",
            },
        )
        assert subject_request.status_code == 201
        manifest = client.post(
            f"/api/v1/tenants/{tenant_id}/subject-rights-requests/"
            f"{subject_request.json()['id']}/export-manifest",
            headers=auth("owner-a"),
            json={"reason": "verified generated subject export request"},
        )
        assert manifest.status_code == 201
        assert manifest.json()["status"] == "metadata_only"
        assert manifest.json()["expires_at"] is not None
        duplicate_manifest = client.post(
            f"/api/v1/tenants/{tenant_id}/subject-rights-requests/"
            f"{subject_request.json()['id']}/export-manifest",
            headers=auth("owner-a"),
            json={"reason": "verified generated duplicate export request"},
        )
        assert duplicate_manifest.status_code == 409
        completed = client.post(
            f"/api/v1/tenants/{tenant_id}/subject-rights-requests/"
            f"{subject_request.json()['id']}/complete",
            headers={**auth("owner-a"), "If-Match": 'W/"1"'},
            json={"reason": "verified generated subject request completion"},
        )
        assert completed.status_code == 200
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/subject-rights-requests/"
                f"{subject_request.json()['id']}",
                headers=auth("owner-a"),
            ).status_code
            == 422
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/subject-rights-requests/"
                f"{subject_request.json()['id']}",
                headers={
                    **auth("owner-a"),
                    "X-Access-Reason": "verified generated subject request read",
                },
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/subject-rights-requests",
                headers={
                    **auth("owner-a"),
                    "X-Access-Reason": "verified generated subject request list",
                },
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/reconciliation-issues",
                headers=auth("owner-a"),
            ).status_code
            == 200
        )


def test_phase3_rejects_prohibited_overposting_and_requires_preconditions() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="phase3-negative", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        prohibited = client.post(
            f"/api/v1/tenants/{tenant_id}/learners",
            headers=auth("owner-a"),
            json={
                "institution_reference": "GEN-LRN-2",
                "name": "Must Not Be Stored",
                "health": "Must Not Be Stored",
            },
        )
        assert prohibited.status_code == 422

        period = client.post(
            f"/api/v1/tenants/{tenant_id}/academic-periods",
            headers=auth("owner-a"),
            json={
                "code": "GEN-T1",
                "name": "Generated",
                "period_type": "term",
                "starts_on": "2026-01-01",
                "ends_on": "2026-03-01",
            },
        )
        stale = client.patch(
            f"/api/v1/tenants/{tenant_id}/academic-periods/{period.json()['id']}",
            headers=auth("owner-a"),
            json={
                "code": "GEN-T1",
                "name": "Generated Updated",
                "period_type": "term",
                "starts_on": "2026-01-01",
                "ends_on": "2026-03-01",
            },
        )
        assert stale.status_code == 428


def test_phase3_reconciliation_requires_mfa_reason_and_version() -> None:
    app = phase2_app()
    with TestClient(app) as client:
        tenant = create_tenant(client, slug="phase3-reconcile", owner_subject="owner-a")
        with Session(app.state.database_engine) as session, session.begin():
            issue = ReconciliationIssue(
                tenant_id=str(tenant["id"]),
                entity_type="learner",
                issue_type="equal_authority_conflict",
                severity="high",
            )
            session.add(issue)
            session.flush()
            issue_id = issue.id
        detail = client.get(
            f"/api/v1/tenants/{tenant['id']}/reconciliation-issues/{issue_id}",
            headers=auth("owner-a"),
        )
        assert detail.status_code == 200
        assert detail.headers["cache-control"] == "no-store"
        resolved = client.post(
            f"/api/v1/tenants/{tenant['id']}/reconciliation-issues/{issue_id}/resolve",
            headers={**auth("owner-a"), "If-Match": 'W/"1"'},
            json={
                "reason": "verified generated source reconciliation",
                "resolution_code": "accept_primary",
            },
        )
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "resolved"
        with Session(app.state.database_engine) as session, session.begin():
            dismissible = ReconciliationIssue(
                tenant_id=str(tenant["id"]),
                entity_type="course",
                issue_type="late_conflict",
                severity="medium",
            )
            session.add(dismissible)
            session.flush()
            dismissible_id = dismissible.id
        dismissed = client.post(
            f"/api/v1/tenants/{tenant['id']}/reconciliation-issues/{dismissible_id}/dismiss",
            headers={**auth("owner-a"), "If-Match": 'W/"1"'},
            json={"reason": "verified generated dismissal"},
        )
        assert dismissed.status_code == 200
        assert dismissed.json()["status"] == "dismissed"
