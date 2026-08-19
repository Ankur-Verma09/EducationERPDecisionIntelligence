from fastapi.testclient import TestClient

from education_erp.ai_test_double import app as ai_test_double


def test_internal_ai_double_is_bounded_and_degraded() -> None:
    with TestClient(ai_test_double) as client:
        assert client.get("/health/live").json() == {
            "status": "ok",
            "service": "ai-contract-test-double",
            "inference_enabled": False,
        }
        ready = client.get("/health/ready")
        assert ready.status_code == 200
        assert ready.json()["status"] == "degraded"
        unavailable = client.post("/internal/v1/generate")
        assert unavailable.status_code == 503
        assert unavailable.json()["code"] == "ai_unavailable"
        assert unavailable.json()["retryable"] is True


def test_core_has_no_ai_dependency(client: TestClient) -> None:
    assert client.get("/api/v1/health/live").status_code == 200
    assert client.get("/api/v1/health/ready").status_code == 200
