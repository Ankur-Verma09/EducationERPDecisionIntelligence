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
    docs_enabled: bool = True
    allowed_hosts: Annotated[tuple[str, ...], NoDecode] = (
        "localhost",
        "127.0.0.1",
        "testserver",
    )

    @field_validator("allowed_hosts", mode="before")
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
        lowered_url = self.database_url.lower()
        if any(marker in lowered_url for marker in ("change-me", "local-only")):
            raise ValueError(
                "deployed environments require externally supplied database credentials"
            )
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
        tls_required = "sslmode=require" in lowered_url or "sslmode=verify-full" in lowered_url
        if not tls_required:
            raise ValueError("deployed database connections require TLS")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide immutable configuration."""

    return Settings()
