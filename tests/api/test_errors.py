from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import LogCaptureFixture

from education_erp.config import Settings
from education_erp.main import create_app


def error_test_app() -> FastAPI:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+pysqlite:///:memory:",
            allowed_hosts=("testserver",),
        )
    )

    @app.get("/test/validate/{value}")
    def validate_value(value: int) -> dict[str, int]:
        return {"value": value}

    @app.get("/test/fail")
    def fail() -> None:
        raise RuntimeError("password=must-not-leak")

    return app


def test_validation_error_uses_public_envelope() -> None:
    with TestClient(error_test_app()) as client:
        response = client.get("/test/validate/not-an-integer")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert "details" in response.json()["error"]


def test_unexpected_error_is_generic_and_retains_security_headers(
    caplog: LogCaptureFixture,
) -> None:
    with TestClient(error_test_app(), raise_server_exceptions=False) as client:
        response = client.get("/test/fail")
    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "internal_error",
        "message": "An unexpected error occurred",
        "request_id": response.headers["x-request-id"],
    }
    assert "must-not-leak" not in response.text
    assert "must-not-leak" not in caplog.text
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_not_found_has_request_id_and_security_headers() -> None:
    with TestClient(error_test_app()) as client:
        response = client.get("/missing")
    assert response.status_code == 404
    assert response.headers["x-request-id"]
    assert response.headers["x-frame-options"] == "DENY"
