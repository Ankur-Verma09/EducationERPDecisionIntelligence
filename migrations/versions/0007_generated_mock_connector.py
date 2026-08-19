"""Add the generated-mock connector framework.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = (
    "connectors",
    "connector_credential_refs",
    "connector_mapping_sets",
    "connector_mapping_versions",
    "connector_sync_jobs",
    "connector_watermarks",
    "connector_batches",
    "connector_staging_records",
    "connector_validation_errors",
    "connector_reconciliation_runs",
    "connector_dead_letters",
)


def _identity(name: str) -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("institutions.id"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "connectors",
        *_identity("connectors"),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind = 'generated_mock_v1'", name="ck_connectors_generated_mock_only"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connectors_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_connectors_tenant_id_name"),
    )
    op.create_table(
        "connector_credential_refs",
        *_identity("connector_credential_refs"),
        sa.Column("connector_id", sa.String(36), nullable=False),
        sa.Column("vault_reference", sa.String(240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("false", name="ck_connector_credential_refs_disabled_in_sprint4"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_credential_refs_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
    )
    op.create_table(
        "connector_mapping_sets",
        *_identity("connector_mapping_sets"),
        sa.Column("connector_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_mapping_sets_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id", "connector_id", "name", name="uq_connector_mapping_set_name"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
    )
    op.create_table(
        "connector_mapping_versions",
        *_identity("connector_mapping_versions"),
        sa.Column("connector_id", sa.String(36), nullable=False),
        sa.Column("mapping_set_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_mapping_versions_tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id", "connector_id", "version", name="uq_connector_mapping_version"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "mapping_set_id"],
            ["connector_mapping_sets.tenant_id", "connector_mapping_sets.id"],
        ),
    )
    op.create_table(
        "connector_sync_jobs",
        *_identity("connector_sync_jobs"),
        sa.Column("connector_id", sa.String(36), nullable=False),
        sa.Column(
            "mapping_version_id",
            sa.String(36),
            nullable=False,
        ),
        sa.Column("scenario", sa.String(40), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("requested_by_user_id", sa.String(36), nullable=False),
        sa.Column("lease_owner", sa.String(120)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("input_count", sa.Integer(), nullable=False),
        sa.Column("accepted_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("failure_code", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_sync_jobs_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "mapping_version_id"],
            ["connector_mapping_versions.tenant_id", "connector_mapping_versions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "requested_by_user_id"],
            ["memberships.tenant_id", "memberships.user_id"],
        ),
        sa.CheckConstraint(
            "attempt >= 0 AND input_count >= 0 AND accepted_count >= 0 "
            "AND rejected_count >= 0 AND duplicate_count >= 0",
            name="ck_connector_sync_jobs_nonnegative",
        ),
    )
    op.create_index(
        "uq_connector_one_active_job",
        "connector_sync_jobs",
        ["connector_id"],
        unique=True,
        postgresql_where=sa.text("state IN ('queued','running')"),
        sqlite_where=sa.text("state IN ('queued','running')"),
    )
    op.create_table(
        "connector_watermarks",
        *_identity("connector_watermarks"),
        sa.Column("connector_id", sa.String(36), nullable=False),
        sa.Column("checkpoint", sa.String(120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "connector_id", name="uq_connector_watermark"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_watermarks_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
    )
    op.create_table(
        "connector_batches",
        *_identity("connector_batches"),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("checkpoint_before", sa.String(120), nullable=False),
        sa.Column("checkpoint_after", sa.String(120), nullable=False),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("input_count", sa.Integer(), nullable=False),
        sa.Column("accepted_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "job_id", "sequence", name="uq_connector_batch_sequence"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_batches_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "job_id"], ["connector_sync_jobs.tenant_id", "connector_sync_jobs.id"]
        ),
    )
    op.create_table(
        "connector_staging_records",
        *_identity("connector_staging_records"),
        sa.Column("connector_id", sa.String(36), nullable=False),
        sa.Column("batch_id", sa.String(36), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("source_key_fingerprint", sa.String(64), nullable=False),
        sa.Column("source_record_version", sa.String(80), nullable=False),
        sa.Column("deduplication_key", sa.String(64), nullable=False),
        sa.Column("normalized_document", sa.JSON()),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "deduplication_key", name="uq_connector_staging_dedup"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_staging_records_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "connector_id"], ["connectors.tenant_id", "connectors.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "batch_id"], ["connector_batches.tenant_id", "connector_batches.id"]
        ),
    )
    op.create_table(
        "connector_validation_errors",
        *_identity("connector_validation_errors"),
        sa.Column(
            "staging_record_id",
            sa.String(36),
            nullable=False,
        ),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("field_path", sa.String(160), nullable=False),
        sa.Column("rule_version", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_validation_errors_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "staging_record_id"],
            ["connector_staging_records.tenant_id", "connector_staging_records.id"],
        ),
    )
    op.create_table(
        "connector_reconciliation_runs",
        *_identity("connector_reconciliation_runs"),
        sa.Column(
            "job_id",
            sa.String(36),
            nullable=False,
        ),
        sa.Column("expected_count", sa.Integer(), nullable=False),
        sa.Column("input_count", sa.Integer(), nullable=False),
        sa.Column("accepted_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("disposition", sa.String(24), nullable=False),
        sa.Column("threshold_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_connector_reconciliation_runs_tenant_id_id"
        ),
        sa.UniqueConstraint("tenant_id", "job_id", name="uq_connector_reconciliation_job"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "job_id"], ["connector_sync_jobs.tenant_id", "connector_sync_jobs.id"]
        ),
    )
    op.create_table(
        "connector_dead_letters",
        *_identity("connector_dead_letters"),
        sa.Column(
            "staging_record_id",
            sa.String(36),
            nullable=False,
        ),
        sa.Column("failure_code", sa.String(80), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("replay_state", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_connector_dead_letters_tenant_id_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "staging_record_id"],
            ["connector_staging_records.tenant_id", "connector_staging_records.id"],
        ),
    )
    if op.get_bind().dialect.name == "postgresql":
        for table in TENANT_TABLES:
            op.execute(f'CREATE INDEX "ix_{table}_tenant_id" ON "{table}" (tenant_id)')
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(
                f'CREATE POLICY "{table}_tenant_isolation" ON "{table}" '
                "USING (tenant_id = current_setting('app.tenant_id', true)) "
                "WITH CHECK (tenant_id = current_setting('app.tenant_id', true))"
            )
            op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON "{table}" TO education_erp_app')
        op.execute(
            "CREATE FUNCTION prevent_connector_tenant_mutation() RETURNS trigger "
            "LANGUAGE plpgsql AS $$ BEGIN IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id "
            "THEN RAISE EXCEPTION 'connector tenant_id is immutable'; END IF; RETURN NEW; END $$"
        )
        for table in TENANT_TABLES:
            op.execute(
                f'CREATE TRIGGER "{table}_tenant_immutable" BEFORE UPDATE ON "{table}" '
                "FOR EACH ROW EXECUTE FUNCTION prevent_connector_tenant_mutation()"
            )
        op.execute(
            "CREATE FUNCTION prevent_connector_history_mutation() RETURNS trigger "
            "LANGUAGE plpgsql AS $$ BEGIN "
            "IF TG_TABLE_NAME = 'connector_batches' AND TG_OP = 'UPDATE' "
            "AND OLD.state = 'processing' AND NEW.state IN ('processing','completed') "
            "AND OLD.id = NEW.id AND OLD.tenant_id = NEW.tenant_id "
            "AND OLD.job_id = NEW.job_id AND OLD.sequence = NEW.sequence "
            "AND OLD.checkpoint_before = NEW.checkpoint_before "
            "AND OLD.checkpoint_after = NEW.checkpoint_after "
            "AND OLD.input_count = NEW.input_count THEN RETURN NEW; END IF; "
            "RAISE EXCEPTION "
            "'connector history is immutable'; END $$"
        )
        for table in ("connector_mapping_versions", "connector_batches"):
            op.execute(
                f'CREATE TRIGGER "{table}_append_only" BEFORE UPDATE OR DELETE '
                f'ON "{table}" FOR EACH ROW EXECUTE FUNCTION '
                "prevent_connector_history_mutation()"
            )
        for table in (
            "connector_mapping_versions",
            "connector_validation_errors",
            "connector_reconciliation_runs",
        ):
            op.execute(f'REVOKE UPDATE, DELETE ON "{table}" FROM education_erp_app')
        for permission in (
            "connector:read",
            "connector:manage",
            "connector:run",
            "connector:reconcile",
            "connector:replay",
        ):
            op.execute(
                sa.text(
                    "INSERT INTO permissions "
                    "(id,name,description,requires_mfa,requires_recent_auth) VALUES "
                    "(gen_random_uuid()::text,:name,:name,:mfa,:recent) "
                    "ON CONFLICT (name) DO NOTHING"
                ).bindparams(
                    name=permission,
                    mfa=permission == "connector:replay",
                    recent=permission == "connector:replay",
                )
            )
        op.execute(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
            "WHERE r.name = 'tenant_owner' AND p.name LIKE 'connector:%' "
            "ON CONFLICT DO NOTHING"
        )
        op.execute(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
            "WHERE r.name = 'registrar' AND p.name IN "
            "('connector:read','connector:run','connector:reconcile','connector:replay') "
            "ON CONFLICT DO NOTHING"
        )
        op.execute(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
            "WHERE r.name = 'auditor' AND p.name = 'connector:read' "
            "ON CONFLICT DO NOTHING"
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS prevent_connector_tenant_mutation() CASCADE")
        op.execute("DROP FUNCTION IF EXISTS prevent_connector_history_mutation() CASCADE")
    op.drop_index("uq_connector_one_active_job", table_name="connector_sync_jobs")
    for table in reversed(TENANT_TABLES):
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{table}"'))
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE name LIKE 'connector:%')"
        )
        op.execute("DELETE FROM permissions WHERE name LIKE 'connector:%'")
