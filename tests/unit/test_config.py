import pytest
from pydantic import ValidationError

from education_erp.config import Settings


def test_settings_parse_comma_separated_hosts() -> None:
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        allowed_hosts="localhost, example.test",  # type: ignore[arg-type]
    )
    assert settings.allowed_hosts == ("localhost", "example.test")


def test_settings_parse_comma_separated_hosts_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDUERP_ALLOWED_HOSTS", "localhost,127.0.0.1,api")
    settings = Settings(database_url="sqlite+pysqlite:///:memory:")
    assert settings.allowed_hosts == ("localhost", "127.0.0.1", "api")


def test_settings_reject_empty_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="")


def test_settings_reject_invalid_connect_timeout() -> None:
    with pytest.raises(ValidationError):
        Settings(database_connect_timeout_seconds=0)


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_deployed_environment_rejects_local_defaults(environment: str) -> None:
    with pytest.raises(ValidationError):
        Settings(environment=environment)  # type: ignore[arg-type]


def test_production_accepts_explicit_safe_configuration() -> None:
    settings = Settings(
        environment="production",
        database_url=(
            "postgresql+psycopg://service:external@database.internal/education_erp?sslmode=require"
        ),
        allowed_hosts=("api.example.edu",),
        docs_enabled=False,
        oidc_issuer_url="https://identity.example",
        oidc_audience="education-api",
        cursor_signing_key="externally-managed-cursor-signing-key",
        demo_connector_enabled=False,
    )
    assert settings.environment == "production"
    assert settings.docs_enabled is False
    assert settings.demo_connector_enabled is False


def test_production_rejects_enabled_demo_connector() -> None:
    with pytest.raises(ValidationError, match="demo connector"):
        Settings(
            environment="production",
            database_url=(
                "postgresql+psycopg://service:external@database.internal/education_erp"
                "?sslmode=require"
            ),
            allowed_hosts=("api.example.edu",),
            docs_enabled=False,
            oidc_issuer_url="https://identity.example",
            oidc_audience="education-api",
            cursor_signing_key="externally-managed-cursor-signing-key",
        )


def test_production_rejects_wildcard_host() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            database_url=(
                "postgresql+psycopg://service:external@database.internal/education_erp"
                "?sslmode=require"
            ),
            allowed_hosts=("*",),
            docs_enabled=False,
        )
