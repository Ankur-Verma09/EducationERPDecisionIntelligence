"""Generated-mock connector framework persistence models."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from education_erp.persistence.base import Base
from education_erp.persistence.models import new_id, utc_now


def tenant_identity(name: str) -> tuple[UniqueConstraint]:
    return (UniqueConstraint("tenant_id", "id", name=f"uq_{name}_tenant_id_id"),)


class Connector(Base):
    __tablename__ = "connectors"
    __table_args__ = (
        *tenant_identity("connectors"),
        UniqueConstraint("tenant_id", "name", name="uq_connectors_tenant_id_name"),
        CheckConstraint(
            "kind IN ('generated_mock_v1','synthetic_reference_erp_v1')",
            name="demo_connector_kinds_only",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(40), default="generated_mock_v1")
    status: Mapped[str] = mapped_column(String(24), default="active")
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SourceSchema(Base):
    __tablename__ = "connector_source_schemas"
    __table_args__ = (
        *tenant_identity("connector_source_schemas"),
        UniqueConstraint(
            "tenant_id", "connector_id", "package_version", name="uq_connector_source_schema"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
        CheckConstraint(
            "package_id = 'synthetic-reference-erp-v1' AND package_version = '1.0.0'",
            name="source_schema_demo_only",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    connector_id: Mapped[str] = mapped_column(String(36))
    package_id: Mapped[str] = mapped_column(String(80))
    package_version: Mapped[str] = mapped_column(String(32))
    schema_version: Mapped[str] = mapped_column(String(16))
    schema_checksum: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="verified")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TransportConfig(Base):
    __tablename__ = "connector_transport_configs"
    __table_args__ = (
        *tenant_identity("connector_transport_configs"),
        UniqueConstraint("tenant_id", "connector_id", name="uq_connector_transport_config"),
        ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
        CheckConstraint(
            "kind = 'in_process_csv_test_double' AND network_egress = false "
            "AND credential_reference IS NULL",
            name="transport_demo_only",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    connector_id: Mapped[str] = mapped_column(String(36))
    kind: Mapped[str] = mapped_column(String(48))
    network_egress: Mapped[bool] = mapped_column(Boolean, default=False)
    credential_reference: Mapped[str | None] = mapped_column(String(240))
    page_size: Mapped[int] = mapped_column(Integer, default=100)
    max_record_bytes: Mapped[int] = mapped_column(Integer, default=65_536)
    max_batch_bytes: Mapped[int] = mapped_column(Integer, default=5_242_880)
    read_timeout_seconds: Mapped[int] = mapped_column(Integer, default=15)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    backoff_seconds: Mapped[list[int]] = mapped_column(JSON, default=lambda: [1, 2, 4])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class MappingSet(Base):
    __tablename__ = "connector_mapping_sets"
    __table_args__ = (
        *tenant_identity("connector_mapping_sets"),
        UniqueConstraint("tenant_id", "connector_id", "name", name="uq_connector_mapping_set_name"),
        ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    connector_id: Mapped[str] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class MappingVersion(Base):
    __tablename__ = "connector_mapping_versions"
    __table_args__ = (
        *tenant_identity("connector_mapping_versions"),
        UniqueConstraint(
            "tenant_id", "connector_id", "version", name="uq_connector_mapping_version"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "mapping_set_id"],
            ["connector_mapping_sets.tenant_id", "connector_mapping_sets.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_schema_id"],
            ["connector_source_schemas.tenant_id", "connector_source_schemas.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    connector_id: Mapped[str] = mapped_column(String(36))
    mapping_set_id: Mapped[str] = mapped_column(String(36))
    source_schema_id: Mapped[str | None] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(16), default="1")
    policy_version: Mapped[str] = mapped_column(String(16), default="1")
    document: Mapped[dict[str, Any]] = mapped_column(JSON)
    checksum: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SyncJob(Base):
    __tablename__ = "connector_sync_jobs"
    __table_args__ = (
        *tenant_identity("connector_sync_jobs"),
        ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "mapping_version_id"],
            ["connector_mapping_versions.tenant_id", "connector_mapping_versions.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "requested_by_user_id"],
            ["memberships.tenant_id", "memberships.user_id"],
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    connector_id: Mapped[str] = mapped_column(String(36), index=True)
    mapping_version_id: Mapped[str] = mapped_column(String(36))
    scenario: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(24), default="queued")
    requested_by_user_id: Mapped[str] = mapped_column(String(36))
    lease_owner: Mapped[str | None] = mapped_column(String(120))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    input_count: Mapped[int] = mapped_column(Integer, default=0)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_code: Mapped[str | None] = mapped_column(String(80))
    package_version_snapshot: Mapped[str | None] = mapped_column(String(32))
    schema_version_snapshot: Mapped[str | None] = mapped_column(String(16))
    threshold_version_snapshot: Mapped[str | None] = mapped_column(String(16))
    test_clock: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    freshness_watermark: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConnectorWatermark(Base):
    __tablename__ = "connector_watermarks"
    __table_args__ = (
        *tenant_identity("connector_watermarks"),
        UniqueConstraint("tenant_id", "connector_id", name="uq_connector_watermark"),
        ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    connector_id: Mapped[str] = mapped_column(String(36))
    checkpoint: Mapped[str] = mapped_column(String(120), default="0")
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ConnectorBatch(Base):
    __tablename__ = "connector_batches"
    __table_args__ = (
        *tenant_identity("connector_batches"),
        UniqueConstraint("tenant_id", "job_id", "sequence", name="uq_connector_batch_sequence"),
        ForeignKeyConstraint(
            ["tenant_id", "job_id"], ["connector_sync_jobs.tenant_id", "connector_sync_jobs.id"]
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    job_id: Mapped[str] = mapped_column(String(36))
    sequence: Mapped[int] = mapped_column(Integer)
    checkpoint_before: Mapped[str] = mapped_column(String(120))
    checkpoint_after: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(24))
    input_count: Mapped[int] = mapped_column(Integer)
    accepted_count: Mapped[int] = mapped_column(Integer)
    rejected_count: Mapped[int] = mapped_column(Integer)
    duplicate_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class StagingRecord(Base):
    __tablename__ = "connector_staging_records"
    __table_args__ = (
        *tenant_identity("connector_staging_records"),
        UniqueConstraint("tenant_id", "deduplication_key", name="uq_connector_staging_dedup"),
        ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"], ["connector_batches.tenant_id", "connector_batches.id"]
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    connector_id: Mapped[str] = mapped_column(String(36))
    batch_id: Mapped[str] = mapped_column(String(36))
    entity_type: Mapped[str] = mapped_column(String(40))
    source_key_fingerprint: Mapped[str] = mapped_column(String(64))
    source_record_version: Mapped[str] = mapped_column(String(80))
    deduplication_key: Mapped[str] = mapped_column(String(64))
    normalized_document: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    outcome: Mapped[str] = mapped_column(String(24))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retention_class: Mapped[str] = mapped_column(String(24), default="landing-24h")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ValidationError(Base):
    __tablename__ = "connector_validation_errors"
    __table_args__ = (
        *tenant_identity("connector_validation_errors"),
        ForeignKeyConstraint(
            ["tenant_id", "staging_record_id"],
            ["connector_staging_records.tenant_id", "connector_staging_records.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    staging_record_id: Mapped[str] = mapped_column(String(36))
    code: Mapped[str] = mapped_column(String(80))
    field_path: Mapped[str] = mapped_column(String(160))
    rule_version: Mapped[str] = mapped_column(String(16), default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReconciliationRun(Base):
    __tablename__ = "connector_reconciliation_runs"
    __table_args__ = (
        *tenant_identity("connector_reconciliation_runs"),
        UniqueConstraint("tenant_id", "job_id", name="uq_connector_reconciliation_job"),
        ForeignKeyConstraint(
            ["tenant_id", "job_id"], ["connector_sync_jobs.tenant_id", "connector_sync_jobs.id"]
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    job_id: Mapped[str] = mapped_column(String(36))
    expected_count: Mapped[int] = mapped_column(Integer)
    input_count: Mapped[int] = mapped_column(Integer)
    accepted_count: Mapped[int] = mapped_column(Integer)
    rejected_count: Mapped[int] = mapped_column(Integer)
    duplicate_count: Mapped[int] = mapped_column(Integer)
    disposition: Mapped[str] = mapped_column(String(24))
    threshold_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    measurements: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    breach_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DeadLetter(Base):
    __tablename__ = "connector_dead_letters"
    __table_args__ = (
        *tenant_identity("connector_dead_letters"),
        ForeignKeyConstraint(
            ["tenant_id", "staging_record_id"],
            ["connector_staging_records.tenant_id", "connector_staging_records.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id"), index=True)
    staging_record_id: Mapped[str] = mapped_column(String(36))
    failure_code: Mapped[str] = mapped_column(String(80))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    replay_state: Mapped[str] = mapped_column(String(24), default="available")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
