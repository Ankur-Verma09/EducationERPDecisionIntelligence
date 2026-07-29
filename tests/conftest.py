from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from education_erp.config import Settings
from education_erp.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        allowed_hosts=("testserver",),
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)
    with app.state.database_engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0001')"))
    with TestClient(app) as test_client:
        yield test_client
