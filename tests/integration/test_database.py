import os

import pytest
from sqlalchemy import create_engine, text

from education_erp.database import EXPECTED_DATABASE_REVISION, database_is_ready


@pytest.mark.integration
def test_database_readiness_executes_query() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                {"revision": EXPECTED_DATABASE_REVISION},
            )
        assert database_is_ready(engine) is True
    finally:
        engine.dispose()


@pytest.mark.integration
def test_database_readiness_rejects_stale_revision() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('stale')"))
        assert database_is_ready(engine) is False
    finally:
        engine.dispose()


@pytest.mark.integration
def test_postgresql_database_is_ready_after_migration() -> None:
    database_url = os.getenv("EDUERP_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("EDUERP_TEST_DATABASE_URL is required for PostgreSQL integration")
    engine = create_engine(database_url)
    try:
        assert engine.dialect.name == "postgresql"
        assert database_is_ready(engine) is True
    finally:
        engine.dispose()


@pytest.mark.integration
def test_database_readiness_fails_closed() -> None:
    engine = create_engine("sqlite+pysqlite:///missing/parent/database.sqlite")
    try:
        assert database_is_ready(engine) is False
    finally:
        engine.dispose()
