"""Typed application configuration."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings with safe defaults for local development."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EDUERP_",
        extra="ignore",
        case_sensitive=False,
        frozen=True,
    )

    app_name: str = "Education ERP Decision Intelligence API"
    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str = "postgresql+psycopg://education_erp:change-me@localhost:5432/education_erp"
    database_connect_timeout_seconds: int = Field(default=3, ge=1, le=30)
    cursor_signing_key: str = Field(default="local-cursor-signing-key-change-me", min_length=24)
    docs_enabled: bool = True
    demo_connector_enabled: bool = True
    oidc_issuer_url: str | None = None
    oidc_audience: str | None = None
    oidc_algorithms: Annotated[tuple[str, ...], NoDecode] = ("RS256",)
    oidc_jwks_cache_seconds: int = Field(default=300, ge=30, le=3600)
    oidc_clock_skew_seconds: int = Field(default=60, ge=0, le=60)
    privileged_mfa_methods: Annotated[tuple[str, ...], NoDecode] = (
        "mfa",
        "otp",
        "webauthn",
    )
    allowed_hosts: Annotated[tuple[str, ...], NoDecode] = (
        "localhost",
        "127.0.0.1",
        "testserver",
    )

    @field_validator("allowed_hosts", "oidc_algorithms", "privileged_mfa_methods", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value:
            raise ValueError("database_url must not be empty")
        return value

    @model_validator(mode="after")
    def reject_unsafe_deployed_defaults(self) -> "Settings":
        if self.environment not in {"staging", "production"}:
            return self
        if self.demo_connector_enabled:
            raise ValueError("the generated demo connector must be disabled when deployed")
        lowered_url = self.database_url.lower()
        if any(marker in lowered_url for marker in ("change-me", "local-only")):
            raise ValueError(
                "deployed environments require externally supplied database credentials"
            )
        if "change-me" in self.cursor_signing_key:
            raise ValueError("deployed environments require an external cursor signing key")
        if not self.allowed_hosts or any(
            host in {"localhost", "127.0.0.1", "testserver", "*"} for host in self.allowed_hosts
        ):
            raise ValueError("deployed environments require an explicit non-local host allowlist")
        if self.docs_enabled:
            raise ValueError(
                "interactive API documentation must be explicitly disabled when deployed"
            )
        if not self.database_url.startswith("postgresql"):
            raise ValueError("deployed environments require PostgreSQL")
        if not self.oidc_issuer_url or not self.oidc_audience:
            raise ValueError("deployed environments require an OIDC issuer and audience")
        if any(
            algorithm == "none" or algorithm.startswith("HS") for algorithm in self.oidc_algorithms
        ):
            raise ValueError("OIDC algorithms must be asymmetric and explicitly approved")
        tls_required = "sslmode=require" in lowered_url or "sslmode=verify-full" in lowered_url
        if not tls_required:
            raise ValueError("deployed database connections require TLS")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable configuration."""

    return Settings()
