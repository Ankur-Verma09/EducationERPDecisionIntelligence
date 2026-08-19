from fastapi.testclient import TestClient

from tests.api.test_phase3_api import _phase3_foundation
from tests.phase2_helpers import auth, phase2_app


def test_phase3_generated_canonical_isolation_journey() -> None:
    with TestClient(phase2_app()) as client:
        tenant, offering = _phase3_foundation(client)
        tenant_id = str(tenant["id"])
        learner = client.post(
            f"/api/v1/tenants/{tenant_id}/learners",
            headers=auth("owner-a"),
            json={"institution_reference": "GEN-E2E-0042"},
        )
        enrolment = client.post(
            f"/api/v1/tenants/{tenant_id}/offering-enrolments",
            headers=auth("owner-a"),
            json={
                "learner_id": learner.json()["id"],
                "target_id": offering["id"],
                "effective_from": "2026-06-20",
            },
        )
        assert learner.status_code == 201
        assert enrolment.status_code == 201
        assert (
            client.get(f"/api/v1/tenants/{tenant_id}/learners", headers=auth("owner-a"))
            .json()["items"][0]["institution_reference_masked"]
            .endswith("0042")
        )
