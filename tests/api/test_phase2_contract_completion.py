from fastapi.testclient import TestClient

from tests.phase2_helpers import ISSUER, auth, create_tenant, phase2_app


def _invite(client: TestClient, tenant_id: str, subject: str) -> dict[str, object]:
    response = client.post(
        f"/api/v1/tenants/{tenant_id}/memberships",
        headers=auth("owner-a"),
        json={
            "issuer": ISSUER,
            "subject": subject,
            "work_email": f"{subject}@example.test",
            "display_name": subject,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _owner_membership_id(client: TestClient, tenant_id: str, token: str) -> str:
    headers = auth(token)
    memberships = client.get(f"/api/v1/tenants/{tenant_id}/memberships", headers=headers).json()[
        "items"
    ]
    for membership in memberships:
        assignments = client.get(
            f"/api/v1/tenants/{tenant_id}/memberships/{membership['id']}/role-assignments",
            headers=headers,
        ).json()
        if any(assignment["role"] == "tenant_owner" for assignment in assignments):
            return str(membership["id"])
    raise AssertionError("tenant owner membership not found")


def test_persistent_idempotency_replay_and_conflict() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="replay", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        url = f"/api/v1/tenants/{tenant_id}/campuses"
        missing = client.post(
            url,
            headers={"Authorization": "Bearer owner-a"},
            json={"code": "ONE", "name": "One"},
        )
        assert missing.status_code == 428

        headers = {**auth("owner-a"), "Idempotency-Key": "persistent-replay"}
        first = client.post(url, headers=headers, json={"code": "ONE", "name": "One"})
        replay = client.post(url, headers=headers, json={"code": "ONE", "name": "One"})
        conflict = client.post(url, headers=headers, json={"code": "TWO", "name": "Two"})
        assert first.status_code == replay.status_code == 201
        assert replay.json() == first.json()
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "idempotency_conflict"


def test_openapi_documents_idempotency_for_every_mutation() -> None:
    schema = phase2_app().openapi()
    for operations in schema["paths"].values():
        for method, operation in operations.items():
            if method not in {"post", "patch", "delete"}:
                continue
            if operation.get("operationId", "").startswith("reveal_reference_"):
                continue
            headers = {
                parameter["name"].lower()
                for parameter in operation.get("parameters", [])
                if parameter.get("in") == "header"
            }
            assert "idempotency-key" in headers


def test_opaque_pagination_and_remaining_detail_contract() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="contract", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        owner = auth("owner-a")
        campuses = []
        for code in ("ONE", "TWO"):
            created = client.post(
                f"/api/v1/tenants/{tenant_id}/campuses",
                headers=auth("owner-a"),
                json={"code": code, "name": code.title()},
            )
            campuses.append(created.json())
        first_page = client.get(
            f"/api/v1/tenants/{tenant_id}/campuses?limit=1",
            headers=owner,
        )
        cursor = first_page.json()["next_cursor"]
        assert cursor and campuses[0]["id"] not in cursor
        second_page = client.get(
            f"/api/v1/tenants/{tenant_id}/campuses?limit=1&cursor={cursor}",
            headers=owner,
        )
        assert second_page.status_code == 200
        assert second_page.json()["items"][0]["id"] != first_page.json()["items"][0]["id"]
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/campuses?cursor=%",
                headers=owner,
            ).status_code
            == 400
        )

        campus_id = campuses[0]["id"]
        department = client.post(
            f"/api/v1/tenants/{tenant_id}/departments",
            headers=auth("owner-a"),
            json={"campus_id": campus_id, "code": "CS", "name": "Computer Science"},
        ).json()
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/campuses/{campus_id}", headers=owner
            ).status_code
            == 200
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/departments/{department['id']}", headers=owner
            ).status_code
            == 200
        )
        updated = client.patch(
            f"/api/v1/tenants/{tenant_id}/departments/{department['id']}",
            headers={**auth("owner-a"), "If-Match": '"1"'},
            json={"name": "Computing"},
        )
        assert updated.status_code == 200

        membership = _invite(client, tenant_id, "viewer")
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/memberships/{membership['id']}", headers=owner
            ).status_code
            == 200
        )
        assignment = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{membership['id']}/role-assignments",
            headers=auth("owner-a"),
            json={"role": "viewer"},
        )
        assert assignment.status_code == 201
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/memberships/{membership['id']}/role-assignments",
                headers=owner,
            ).json()[0]["role"]
            == "viewer"
        )
        assert client.get("/api/v1/me/memberships", headers=auth("viewer")).status_code == 200
        assert (
            client.get(
                f"/api/v1/platform/institutions/{tenant_id}", headers=auth("admin")
            ).status_code
            == 200
        )
        owner_membership_id = _owner_membership_id(client, tenant_id, "owner-a")
        deletion = client.post(
            f"/api/v1/platform/institutions/{tenant_id}/request-deletion",
            headers=auth("admin"),
            json={
                "reason": "Approved tenant-owner request",
                "tenant_owner_approval_membership_id": owner_membership_id,
            },
        )
        assert deletion.status_code == 200


def test_scoped_delegation_cannot_escape_department_or_tenant() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="scope-a", owner_subject="owner-a")
        other = create_tenant(client, slug="scope-b", owner_subject="owner-b")
        tenant_id = str(tenant["id"])
        first_campus = client.post(
            f"/api/v1/tenants/{tenant_id}/campuses",
            headers=auth("owner-a"),
            json={"code": "ONE", "name": "One"},
        ).json()
        other_campus = client.post(
            f"/api/v1/tenants/{other['id']}/campuses",
            headers=auth("owner-b"),
            json={"code": "OTHER", "name": "Other"},
        ).json()
        first_department = client.post(
            f"/api/v1/tenants/{tenant_id}/departments",
            headers=auth("owner-a"),
            json={"campus_id": first_campus["id"], "code": "ONE", "name": "One"},
        ).json()
        admin_member = _invite(client, tenant_id, "department-admin")
        viewer_member = _invite(client, tenant_id, "viewer")
        delegated = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{admin_member['id']}/role-assignments",
            headers=auth("owner-a"),
            json={
                "role": "department_admin",
                "campus_id": first_campus["id"],
                "department_id": first_department["id"],
            },
        )
        assert delegated.status_code == 201
        cross_tenant = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{viewer_member['id']}/role-assignments",
            headers=auth("department-admin"),
            json={
                "role": "department_admin",
                "campus_id": other_campus["id"],
                "department_id": first_department["id"],
            },
        )
        assert cross_tenant.status_code == 404
        escalation = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{viewer_member['id']}/role-assignments",
            headers=auth("department-admin"),
            json={"role": "tenant_admin"},
        )
        assert escalation.status_code == 403
        in_scope = client.post(
            f"/api/v1/tenants/{tenant_id}/memberships/{viewer_member['id']}/role-assignments",
            headers=auth("department-admin"),
            json={
                "role": "viewer",
                "campus_id": first_campus["id"],
                "department_id": first_department["id"],
            },
        )
        assert in_scope.status_code == 201


def test_completed_contract_negative_boundaries() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="boundaries", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        assert (
            client.get("/api/v1/platform/institutions/missing", headers=auth("admin")).status_code
            == 404
        )
        assert (
            client.get(
                f"/api/v1/platform/institutions/{tenant_id}", headers=auth("owner-a")
            ).status_code
            == 403
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/memberships/missing", headers=auth("owner-a")
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/memberships/missing/role-assignments",
                headers=auth("owner-a"),
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"/api/v1/tenants/{tenant_id}/audit-events",
                headers=auth("owner-a-without-mfa"),
            ).status_code
            == 403
        )
        assert (
            client.patch(
                f"/api/v1/tenants/{tenant_id}/departments/missing",
                headers={**auth("owner-a"), "If-Match": '"1"'},
                json={"name": "Missing"},
            ).status_code
            == 404
        )
        deletion_url = f"/api/v1/platform/institutions/{tenant_id}/request-deletion"
        owner_membership_id = _owner_membership_id(client, tenant_id, "owner-a")
        denied = client.post(
            deletion_url,
            headers=auth("admin"),
            json={
                "reason": "Unapproved request",
                "tenant_owner_approval_membership_id": "missing",
            },
        )
        first = client.post(
            deletion_url,
            headers=auth("admin"),
            json={
                "reason": "Owner approved",
                "tenant_owner_approval_membership_id": owner_membership_id,
            },
        )
        second = client.post(
            deletion_url,
            headers=auth("admin"),
            json={
                "reason": "Owner approved again",
                "tenant_owner_approval_membership_id": owner_membership_id,
            },
        )
        assert denied.status_code == 403
        assert first.status_code == 200
        assert second.status_code == 409
