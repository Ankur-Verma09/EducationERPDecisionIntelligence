from fastapi.testclient import TestClient


def test_foundation_operational_journey(client: TestClient) -> None:
    live = client.get("/api/v1/health/live")
    ready = client.get("/api/v1/health/ready")
    specification = client.get("/openapi.json")

    assert live.status_code == 200
    assert ready.status_code == 200
    assert specification.status_code == 200
    assert live.headers["x-request-id"] != ready.headers["x-request-id"]
