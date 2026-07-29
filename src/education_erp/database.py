"""Database engine creation and readiness checks."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from education_erp.config import Settings

EXPECTED_DATABASE_REVISION = "0001"


def create_database_engine(settings: Settings) -> Engine:
    """Create a pooled SQLAlchemy engine without opening a connection."""

    connect_args: dict[str, object] = {}
    engine_options: dict[str, object] = {}
    if settings.database_url.startswith("postgresql"):
        connect_args["connect_timeout"] = settings.database_connect_timeout_seconds
    if settings.database_url == "sqlite+pysqlite:///:memory:":
        connect_args["check_same_thread"] = False
        engine_options["poolclass"] = StaticPool
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
        **engine_options,
    )


@contextmanager
def checked_connection(engine: Engine) -> Iterator[None]:
    """Yield after verifying the database accepts a trivial query."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        yield


def database_is_ready(
    engine: Engine,
    expected_revision: str = EXPECTED_DATABASE_REVISION,
) -> bool:
    """Verify connectivity and migration revision without leaking driver details."""

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            return str(revision) == expected_revision
    except SQLAlchemyError:
        return False
