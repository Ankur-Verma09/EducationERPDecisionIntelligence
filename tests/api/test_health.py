from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_with_database(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_documents_versioned_health_endpoints(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health/live" in paths
    assert "/api/v1/health/ready" in paths


def test_readiness_rejects_stale_migration(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    with app.state.database_engine.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num = 'stale'"))
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
