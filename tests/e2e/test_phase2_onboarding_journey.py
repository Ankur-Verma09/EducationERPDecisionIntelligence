from fastapi.testclient import TestClient

from tests.phase2_helpers import auth, create_tenant, phase2_app


def test_phase2_onboarding_role_and_isolation_journey() -> None:
    with TestClient(phase2_app()) as client:
        first = create_tenant(client, slug="journey-one", owner_subject="owner-a")
        second = create_tenant(client, slug="journey-two", owner_subject="owner-b")
        tenant_id = str(first["id"])

        membership = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships",
            headers=auth("owner-a"),
            json={
                "issuer": "https://identity.test",
                "subject": "viewer",
                "work_email": "viewer@example.test",
                "display_name": "Viewer",
            },
        )
        assert membership.status_code == 201

        assignment = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{membership.json()['id']}/role-assignments",
            headers=auth("owner-a"),
            json={"role": "viewer"},
        )
        assert assignment.status_code == 201

        own_tenant = client.get(f"/api/v1/tenants/{tenant_id}", headers=auth("viewer"))
        other_tenant = client.get(
            f"/api/v1/tenants/{second['id']}",
            headers=auth("viewer"),
        )
        audit = client.get(
            f"/api/v1/tenants/{tenant_id}/audit-events",
            headers=auth("owner-a"),
        )

    assert own_tenant.status_code == 200
    assert other_tenant.status_code == 404
    assert audit.status_code == 200
    assert {event["action"] for event in audit.json()["items"]} >= {
        "institution.created",
        "membership.created",
        "role.assigned",
    }
