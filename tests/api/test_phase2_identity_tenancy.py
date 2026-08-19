from fastapi.testclient import TestClient

from tests.phase2_helpers import auth, create_tenant, phase2_app


def test_authentication_is_required() -> None:
    with TestClient(phase2_app()) as client:
        response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_invalid_token_is_rejected() -> None:
    with TestClient(phase2_app()) as client:
        response = client.get("/api/v1/me", headers=auth("invalid"))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_platform_admin_onboards_tenant_with_owner_and_audit() -> None:
    with TestClient(phase2_app()) as client:
        tenant = create_tenant(client, slug="north-college", owner_subject="owner-a")
        tenant_id = str(tenant["id"])
        own_tenant = client.get(
            f"/api/v1/tenants/{tenant_id}",
            headers=auth("owner-a"),
        )
        audit = client.get(
            f"/api/v1/tenants/{tenant_id}/audit-events",
            headers=auth("owner-a"),
        )
    assert own_tenant.status_code == 200
    assert audit.status_code == 200
    assert {event["action"] for event in audit.json()["items"]} >= {
        "institution.created",
        "institution.activated",
    }


def test_platform_onboarding_requires_mfa() -> None:
    with TestClient(phase2_app()) as client:
        response = client.post(
            "/api/v1/platform/institutions",
            headers=auth("admin-without-mfa"),
            json={
                "slug": "no-mfa",
                "legal_name": "No MFA",
                "display_name": "No MFA",
                "data_region": "test",
                "initial_owner": {
                    "issuer": "https://identity.test",
                    "subject": "owner-a",
                    "work_email": "owner@example.test",
                    "display_name": "Owner",
                },
            },
        )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "mfa_required"


def test_mass_assignment_is_rejected() -> None:
    with TestClient(phase2_app()) as client:
        response = client.post(
            "/api/v1/platform/institutions",
            headers=auth("admin"),
            json={
                "slug": "mass-assignment",
                "legal_name": "Mass Assignment",
                "display_name": "Mass Assignment",
                "data_region": "test",
                "status": "active",
                "initial_owner": {
                    "issuer": "https://identity.test",
                    "subject": "owner-a",
                    "work_email": "owner@example.test",
                    "display_name": "Owner",
                },
            },
        )
    assert response.status_code == 422
