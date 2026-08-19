from fastapi.testclient import TestClient

from tests.phase2_helpers import ISSUER, auth, create_tenant, phase2_app


def test_phase2_administration_lifecycle() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="extended", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        owner_headers = auth("owner-a")

        platform_list = client.get("/api/v1/platform/institutions", headers=auth("admin"))
        assert platform_list.status_code == 200
        assert platform_list.json()["items"][0]["id"] == tenant_id

        assert (
            client.patch(
                f"/api/v1/tenants/{tenant_id}",
                headers=owner_headers,
                json={"display_name": "Updated"},
            ).status_code
            == 428
        )
        assert (
            client.patch(
                f"/api/v1/tenants/{tenant_id}",
                headers={**owner_headers, "If-Match": '"999"'},
                json={"display_name": "Updated"},
            ).status_code
            == 412
        )
        updated = client.patch(
            f"/api/v1/tenants/{tenant_id}",
            headers={**owner_headers, "If-Match": f'"{tenant["version"]}"'},
            json={"display_name": "Updated"},
        )
        assert updated.status_code == 200
        assert updated.headers["etag"] == '"3"'

        campus = client.post(
            f"/api/v1/tenants/{tenant_id}/campuses",
            headers=owner_headers,
            json={"code": "MAIN", "name": "Main"},
        )
        assert campus.status_code == 201
        campus_id = campus.json()["id"]
        assert (
            client.post(
                f"/api/v1/tenants/{tenant_id}/campuses",
                headers=owner_headers,
                json={"code": "MAIN", "name": "Duplicate"},
            ).status_code
            == 409
        )
        assert (
            len(
                client.get(f"/api/v1/tenants/{tenant_id}/campuses", headers=owner_headers).json()[
                    "items"
                ]
            )
            == 1
        )
        assert (
            client.patch(
                f"/api/v1/tenants/{tenant_id}/campuses/{campus_id}",
                headers=owner_headers,
                json={"name": "Renamed"},
            ).status_code
            == 428
        )
        renamed = client.patch(
            f"/api/v1/tenants/{tenant_id}/campuses/{campus_id}",
            headers={**owner_headers, "If-Match": '"1"'},
            json={"name": "Renamed"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["version"] == 2

        assert (
            client.post(
                f"/api/v1/tenants/{tenant_id}/departments",
                headers=owner_headers,
                json={"campus_id": "missing", "code": "CS", "name": "CS"},
            ).status_code
            == 404
        )
        department = client.post(
            f"/api/v1/tenants/{tenant_id}/departments",
            headers=owner_headers,
            json={"campus_id": campus_id, "code": "CS", "name": "Computer Science"},
        )
        assert department.status_code == 201
        departments = client.get(
            f"/api/v1/tenants/{tenant_id}/departments?campus_id={campus_id}",
            headers=owner_headers,
        )
        assert departments.status_code == 200
        assert departments.json()["items"][0]["id"] == department.json()["id"]

        membership = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships",
            headers=owner_headers,
            json={
                "issuer": ISSUER,
                "subject": "owner-b",
                "work_email": "owner-b@example.test",
                "display_name": "Owner B",
            },
        )
        assert membership.status_code == 201
        membership_id = membership.json()["id"]
        support_user_id = membership.json()["user_id"]
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/memberships", headers=owner_headers
            ).status_code
            == 200
        )
        assert (
            client.get(f"/api/v1/tenants/{tenant_id}/roles", headers=owner_headers).status_code
            == 200
        )

        assignment = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{membership_id}/role-assignments",
            headers=owner_headers,
            json={"role": "viewer"},
        )
        assert assignment.status_code == 201
        assert (
            client.delete(
                f"/api/v1/tenants/{tenant_id}/memberships/{membership_id}"
                f"/role-assignments/{assignment.json()['id']}",
                headers=owner_headers,
            ).status_code
            == 428
        )
        assert (
            client.delete(
                f"/api/v1/tenants/{tenant_id}/memberships/{membership_id}"
                f"/role-assignments/{assignment.json()['id']}",
                headers={
                    **owner_headers,
                    "If-Match": f'"{assignment.json()["version"]}"',
                },
            ).status_code
            == 204
        )

        suspended = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{membership_id}/suspend",
            headers=owner_headers,
        )
        assert suspended.json()["status"] == "suspended"
        activated = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{membership_id}/activate",
            headers=owner_headers,
        )
        assert activated.json()["status"] == "active"

        policy = client.get(f"/api/v1/tenants/{tenant_id}/security-policy", headers=owner_headers)
        assert policy.status_code == 200
        assert (
            client.patch(
                f"/api/v1/tenants/{tenant_id}/security-policy",
                headers=owner_headers,
                json={"mfa_required_for_all": True},
            ).status_code
            == 428
        )
        policy_update = client.patch(
            f"/api/v1/tenants/{tenant_id}/security-policy",
            headers={**owner_headers, "If-Match": policy.headers["etag"]},
            json={"mfa_required_for_all": True, "session_max_minutes": 120},
        )
        assert policy_update.status_code == 200

        grant = client.post(
            f"/api/v1/tenants/{tenant_id}/support-access-grants",
            headers=owner_headers,
            json={
                "support_user_id": support_user_id,
                "reason": "Investigate ticket",
                "ticket_reference": "SEC-123",
                "scope": {"campus_id": campus_id},
                "duration_minutes": 30,
            },
        )
        assert grant.status_code == 201
        grant_id = grant.json()["id"]
        approved = client.post(
            f"/api/v1/tenants/{tenant_id}/support-access-grants/{grant_id}/approve",
            headers=owner_headers,
        )
        assert approved.json()["status"] == "approved"
        assert (
            client.post(
                f"/api/v1/tenants/{tenant_id}/support-access-grants/{grant_id}/approve",
                headers=owner_headers,
            ).status_code
            == 200
        )
        revoked = client.post(
            f"/api/v1/tenants/{tenant_id}/support-access-grants/{grant_id}/revoke",
            headers=owner_headers,
        )
        assert revoked.json()["status"] == "revoked"

        revoked_membership = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{membership_id}/revoke",
            headers=owner_headers,
        )
        assert revoked_membership.json()["status"] == "revoked"

        suspended_tenant = client.post(
            f"/api/v1/platform/institutions/{tenant_id}/suspend",
            headers=auth("admin"),
            json={"reason": "Maintenance"},
        )
        assert suspended_tenant.json()["status"] == "suspended"
        assert client.get(f"/api/v1/tenants/{tenant_id}", headers=owner_headers).status_code == 404
        reactivated = client.post(
            f"/api/v1/platform/institutions/{tenant_id}/activate",
            headers=auth("admin"),
        )
        assert reactivated.json()["status"] == "active"


def test_extended_api_denies_unprivileged_and_invalid_state() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="negative", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        assert (
            client.get("/api/v1/platform/institutions", headers=auth("owner-a")).status_code == 403
        )
        assert (
            client.post(
                f"/api/v1/platform/institutions/{tenant_id}/suspend",
                headers=auth("admin-without-mfa"),
                json={"reason": "No MFA"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                f"/api/v1/tenants/{tenant_id}/memberships/missing/suspend",
                headers=auth("owner-a"),
            ).status_code
            == 404
        )
