from fastapi.testclient import TestClient

from tests.phase2_helpers import auth, create_tenant, phase2_app


def test_cross_tenant_resource_is_hidden() -> None:
    with TestClient(phase2_app()) as client:
        tenant_a = create_tenant(client, slug="tenant-a", owner_subject="owner-a")
        tenant_b = create_tenant(client, slug="tenant-b", owner_subject="owner-b")
        response = client.get(
            f"/api/v1/tenants/{tenant_b['id']}",
            headers=auth("owner-a"),
        )
        same_tenant = client.get(
            f"/api/v1/tenants/{tenant_a['id']}",
            headers=auth("owner-a"),
        )
    assert same_tenant.status_code == 200
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"


def test_unprivileged_membership_cannot_mutate_tenant() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="permission-test", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
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
        assert membership.status_code == 201, membership.text
        assignment = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{membership.json()['id']}/role-assignments",
            headers=auth("owner-a"),
            json={"role": "viewer"},
        )
        assert assignment.status_code == 201, assignment.text
        visible = client.get(f"/api/v1/tenants/{tenant_id}", headers=auth("viewer"))
        denied = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships",
            headers=auth("viewer"),
            json={
                "issuer": "https://identity.test",
                "subject": "another",
                "work_email": "another@example.test",
                "display_name": "Another",
            },
        )
    assert visible.status_code == 200
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "permission_denied"
