"""Add the approved synthetic-reference demo connector profile.

Revision ID: 0008
Revises: 0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_TABLES = ("connector_source_schemas", "connector_transport_configs")


def _tenant_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("institutions.id"), nullable=False),
    ]


def upgrade() -> None:
    op.drop_constraint("ck_connectors_generated_mock_only", "connectors", type_="check")
    op.create_check_constraint(
        "ck_connectors_demo_kinds_only",
        "connectors",
        "kind IN ('generated_mock_v1','synthetic_reference_erp_v1')",
    )
    op.create_table(
        "connector_source_schemas",
        *_tenant_columns(),
        sa.Column("connector_id", sa.String(36), nullable=False),
        sa.Column("package_id", sa.String(80), nullable=False),
        sa.Column("package_version", sa.String(32), nullable=False),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("schema_checksum", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "package_id = 'synthetic-reference-erp-v1' AND package_version = '1.0.0' "
            "AND schema_version = '1' AND status IN ('verified','rejected')",
            name="ck_connector_source_schema_demo_only",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_source_schemas_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id", "connector_id", "package_version", name="uq_connector_source_schema"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
    )
    op.create_table(
        "connector_transport_configs",
        *_tenant_columns(),
        sa.Column("connector_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(48), nullable=False),
        sa.Column("network_egress", sa.Boolean(), nullable=False),
        sa.Column("credential_reference", sa.String(240)),
        sa.Column("page_size", sa.Integer(), nullable=False),
        sa.Column("max_record_bytes", sa.Integer(), nullable=False),
        sa.Column("max_batch_bytes", sa.Integer(), nullable=False),
        sa.Column("read_timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("backoff_seconds", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind = 'in_process_csv_test_double' AND network_egress = false "
            "AND credential_reference IS NULL AND page_size = 100 "
            "AND max_record_bytes = 65536 AND max_batch_bytes = 5242880 "
            "AND read_timeout_seconds = 15 AND max_attempts = 3",
            name="ck_connector_transport_demo_only",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_transport_configs_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "connector_id", name="uq_connector_transport_config"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
    )
    op.add_column(
        "connector_mapping_versions",
        sa.Column("source_schema_id", sa.String(36), nullable=True),
    )
    op.add_column(
        "connector_mapping_versions",
        sa.Column("policy_version", sa.String(16), nullable=False, server_default="1"),
    )
    op.create_foreign_key(
        "fk_mapping_source_schema",
        "connector_mapping_versions",
        "connector_source_schemas",
        ["tenant_id", "source_schema_id"],
        ["tenant_id", "id"],
    )
    for name, type_ in (
        ("package_version_snapshot", sa.String(32)),
        ("schema_version_snapshot", sa.String(16)),
        ("threshold_version_snapshot", sa.String(16)),
        ("test_clock", sa.DateTime(timezone=True)),
        ("freshness_watermark", sa.DateTime(timezone=True)),
    ):
        op.add_column("connector_sync_jobs", sa.Column(name, type_, nullable=True))
    op.add_column(
        "connector_staging_records", sa.Column("source_updated_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "connector_staging_records", sa.Column("effective_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "connector_staging_records",
        sa.Column("retention_class", sa.String(24), nullable=False, server_default="landing-24h"),
    )
    op.execute(
        "UPDATE connector_staging_records AS staging SET retention_class = 'quarantine-7d' "
        "FROM connectors AS connector WHERE staging.connector_id = connector.id "
        "AND staging.tenant_id = connector.tenant_id AND connector.kind = 'generated_mock_v1'"
    )
    op.add_column("outbox_events", sa.Column("correlation_id", sa.String(36), nullable=True))
    op.add_column("outbox_events", sa.Column("causation_id", sa.String(36), nullable=True))
    op.add_column(
        "connector_reconciliation_runs",
        sa.Column("measurements", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "connector_reconciliation_runs",
        sa.Column("breach_codes", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    if op.get_bind().dialect.name == "postgresql":
        op.create_check_constraint(
            "ck_connector_staging_retention_window",
            "connector_staging_records",
            "(retention_class = 'landing-24h' AND expires_at <= created_at + INTERVAL '24 hours') "
            "OR (retention_class = 'quarantine-7d' "
            "AND expires_at <= created_at + INTERVAL '7 days')",
        )
        for table in NEW_TABLES:
            op.execute(f'CREATE INDEX "ix_{table}_tenant_id" ON "{table}" (tenant_id)')
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(
                f'CREATE POLICY "{table}_tenant_isolation" ON "{table}" '
                "USING (tenant_id = current_setting('app.tenant_id', true)) "
                "WITH CHECK (tenant_id = current_setting('app.tenant_id', true))"
            )
            op.execute(f'GRANT SELECT, INSERT ON "{table}" TO education_erp_app')
            op.execute(
                f'CREATE TRIGGER "{table}_tenant_immutable" BEFORE UPDATE ON "{table}" '
                "FOR EACH ROW EXECUTE FUNCTION prevent_connector_tenant_mutation()"
            )
            op.execute(
                f'CREATE TRIGGER "{table}_append_only" BEFORE UPDATE OR DELETE ON "{table}" '
                "FOR EACH ROW EXECUTE FUNCTION prevent_connector_history_mutation()"
            )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE connector_staging_records DROP CONSTRAINT IF EXISTS "
            "ck_connector_staging_records_ck_connector_staging_reten_d788"
        )
        op.execute("ALTER TABLE outbox_events DROP COLUMN IF EXISTS causation_id")
        op.execute("ALTER TABLE outbox_events DROP COLUMN IF EXISTS correlation_id")
    else:
        op.drop_column("outbox_events", "causation_id")
        op.drop_column("outbox_events", "correlation_id")
    for name in ("breach_codes", "measurements"):
        op.drop_column("connector_reconciliation_runs", name)
    for name in ("retention_class", "effective_at", "source_updated_at"):
        op.drop_column("connector_staging_records", name)
    for name in (
        "freshness_watermark",
        "test_clock",
        "threshold_version_snapshot",
        "schema_version_snapshot",
        "package_version_snapshot",
    ):
        op.drop_column("connector_sync_jobs", name)
    op.drop_constraint("fk_mapping_source_schema", "connector_mapping_versions", type_="foreignkey")
    op.drop_column("connector_mapping_versions", "policy_version")
    op.drop_column("connector_mapping_versions", "source_schema_id")
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
    op.drop_constraint("ck_connectors_demo_kinds_only", "connectors", type_="check")
    op.create_check_constraint(
        "ck_connectors_generated_mock_only", "connectors", "kind = 'generated_mock_v1'"
    )
