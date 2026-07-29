from uuid import UUID

from fastapi.testclient import TestClient


def test_response_contains_security_headers_and_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert str(UUID(response.headers["x-request-id"])) == response.headers["x-request-id"]


def test_valid_request_id_is_propagated(client: TestClient) -> None:
    request_id = "c7ea2964-554f-4eed-98cc-49c1fdc41926"
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": request_id})
    assert response.headers["x-request-id"] == request_id


def test_untrusted_host_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"host": "attacker.example"})
    assert response.status_code == 400
