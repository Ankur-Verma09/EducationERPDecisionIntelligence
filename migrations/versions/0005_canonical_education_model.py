"""Add the Phase 3 canonical education model.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "academic_periods",
    "programmes",
    "programme_versions",
    "courses",
    "course_versions",
    "offerings",
    "teaching_assignments",
    "learners",
    "programme_enrolments",
    "offering_enrolments",
    "enrolment_status_history",
    "source_systems",
    "source_authority_rules",
    "source_observations",
    "learner_lineage_links",
    "reconciliation_issues",
    "subject_rights_requests",
    "subject_export_manifests",
)

LINEAGE_TARGETS = {
    "academic_period_lineage_links": ("academic_periods", "academic_period_id"),
    "programme_lineage_links": ("programmes", "programme_id"),
    "programme_version_lineage_links": ("programme_versions", "programme_version_id"),
    "course_lineage_links": ("courses", "course_id"),
    "course_version_lineage_links": ("course_versions", "course_version_id"),
    "offering_lineage_links": ("offerings", "offering_id"),
    "programme_enrolment_lineage_links": (
        "programme_enrolments",
        "programme_enrolment_id",
    ),
    "offering_enrolment_lineage_links": (
        "offering_enrolments",
        "offering_enrolment_id",
    ),
}

PHASE3_ROLE_PERMISSIONS = {
    "tenant_owner": {
        "academic_structure:read",
        "academic_structure:manage",
        "learner:read",
        "learner:manage",
        "learner_identifier:read",
        "enrolment:read",
        "enrolment:manage",
        "lineage:read",
        "reconciliation:manage",
        "subject_rights:read",
        "subject_rights:manage",
        "subject_export:create",
    },
    "tenant_admin": {"academic_structure:read", "academic_structure:manage"},
    "auditor": {"academic_structure:read", "learner:read", "enrolment:read", "lineage:read"},
    "registrar": {
        "academic_structure:read",
        "academic_structure:manage",
        "learner:read",
        "learner:manage",
        "learner_identifier:read",
        "enrolment:read",
        "enrolment:manage",
        "lineage:read",
        "reconciliation:manage",
        "subject_rights:read",
        "subject_rights:manage",
        "subject_export:create",
    },
    "department_admin": {
        "academic_structure:read",
        "academic_structure:manage",
        "learner:read",
        "enrolment:read",
        "enrolment:manage",
    },
    "viewer": {"academic_structure:read"},
}


def _id() -> sa.Column[str]:
    return sa.Column("id", sa.String(36), primary_key=True)


def _tenant(*, foreign_key: bool = False) -> sa.Column[str]:
    args = (sa.ForeignKey("institutions.id"),) if foreign_key else ()
    return sa.Column("tenant_id", sa.String(36), *args, nullable=False, index=True)


def _mutable() -> tuple[sa.Column[Any], sa.Column[Any], sa.Column[Any]]:
    return (
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def _tenant_id_unique(table: str) -> sa.UniqueConstraint:
    return sa.UniqueConstraint("tenant_id", "id", name=f"uq_{table}_tenant_id_id")


def _interval() -> sa.CheckConstraint:
    return sa.CheckConstraint(
        "effective_to IS NULL OR effective_to > effective_from",
        name="valid_interval",
    )


def _create_phase3_tables() -> None:
    """Create the immutable revision-owned Phase 3 schema."""

    op.create_table(
        "academic_periods",
        _id(),
        _tenant(foreign_key=True),
        sa.Column("parent_period_id", sa.String(36)),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("period_type", sa.String(24), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        *_mutable(),
        _tenant_id_unique("academic_periods"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_academic_periods_tenant_id_code"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "parent_period_id"],
            ["academic_periods.tenant_id", "academic_periods.id"],
        ),
        sa.CheckConstraint("ends_on >= starts_on", name="valid_interval"),
    )
    op.create_table(
        "programmes",
        _id(),
        _tenant(foreign_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        *_mutable(),
        _tenant_id_unique("programmes"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_programmes_tenant_id_code"),
    )
    op.create_table(
        "programme_versions",
        _id(),
        _tenant(),
        sa.Column("programme_id", sa.String(36), nullable=False),
        sa.Column("version_code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("status", sa.String(24), nullable=False),
        *_mutable(),
        _tenant_id_unique("programme_versions"),
        sa.UniqueConstraint(
            "tenant_id",
            "programme_id",
            "version_code",
            name="uq_programme_versions_programme_version",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "programme_id"], ["programmes.tenant_id", "programmes.id"]
        ),
        _interval(),
    )
    op.create_table(
        "courses",
        _id(),
        _tenant(foreign_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        *_mutable(),
        _tenant_id_unique("courses"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_courses_tenant_id_code"),
    )
    op.create_table(
        "course_versions",
        _id(),
        _tenant(),
        sa.Column("course_id", sa.String(36), nullable=False),
        sa.Column("version_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("credit_value", sa.Numeric(5, 2)),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("status", sa.String(24), nullable=False),
        *_mutable(),
        _tenant_id_unique("course_versions"),
        sa.UniqueConstraint(
            "tenant_id",
            "course_id",
            "version_code",
            name="uq_course_versions_course_version",
        ),
        sa.ForeignKeyConstraint(["tenant_id", "course_id"], ["courses.tenant_id", "courses.id"]),
        _interval(),
    )
    op.create_table(
        "offerings",
        _id(),
        _tenant(),
        sa.Column("academic_period_id", sa.String(36), nullable=False),
        sa.Column("course_version_id", sa.String(36), nullable=False),
        sa.Column("campus_id", sa.String(36)),
        sa.Column("department_id", sa.String(36)),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        *_mutable(),
        _tenant_id_unique("offerings"),
        sa.UniqueConstraint(
            "tenant_id",
            "academic_period_id",
            "code",
            name="uq_offerings_period_code",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "academic_period_id"],
            ["academic_periods.tenant_id", "academic_periods.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "course_version_id"],
            ["course_versions.tenant_id", "course_versions.id"],
        ),
    )
    op.create_table(
        "teaching_assignments",
        _id(),
        _tenant(),
        sa.Column("offering_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role_code", sa.String(32), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        *_mutable(),
        _tenant_id_unique("teaching_assignments"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "offering_id"], ["offerings.tenant_id", "offerings.id"]
        ),
        _interval(),
    )
    op.create_table(
        "learners",
        _id(),
        _tenant(foreign_key=True),
        sa.Column("institution_reference", sa.String(200), nullable=False),
        sa.Column("institution_reference_fingerprint", sa.String(64), nullable=False),
        sa.Column("platform_user_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("processing_restricted", sa.Boolean(), nullable=False),
        sa.Column("restriction_reason_code", sa.String(64)),
        sa.Column("retention_class", sa.String(32), nullable=False),
        sa.Column("deletion_eligible_at", sa.DateTime(timezone=True)),
        *_mutable(),
        _tenant_id_unique("learners"),
        sa.UniqueConstraint(
            "tenant_id",
            "institution_reference_fingerprint",
            name="uq_learners_tenant_reference",
        ),
    )
    for table, target, target_table in (
        ("programme_enrolments", "programme_version_id", "programme_versions"),
        ("offering_enrolments", "offering_id", "offerings"),
    ):
        op.create_table(
            table,
            _id(),
            _tenant(),
            sa.Column("learner_id", sa.String(36), nullable=False),
            sa.Column(target, sa.String(36), nullable=False),
            sa.Column("status", sa.String(24), nullable=False),
            sa.Column("effective_from", sa.Date(), nullable=False),
            sa.Column("effective_to", sa.Date()),
            *_mutable(),
            _tenant_id_unique(table),
            sa.ForeignKeyConstraint(
                ["tenant_id", "learner_id"], ["learners.tenant_id", "learners.id"]
            ),
            sa.ForeignKeyConstraint(
                ["tenant_id", target], [f"{target_table}.tenant_id", f"{target_table}.id"]
            ),
            _interval(),
        )
    op.create_table(
        "enrolment_status_history",
        _id(),
        _tenant(foreign_key=True),
        sa.Column("enrolment_type", sa.String(16), nullable=False),
        sa.Column("enrolment_id", sa.String(36), nullable=False),
        sa.Column("from_status", sa.String(24), nullable=False),
        sa.Column("to_status", sa.String(24), nullable=False),
        sa.Column("reason_code", sa.String(40), nullable=False),
        sa.Column(
            "changed_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "source_systems",
        _id(),
        _tenant(foreign_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        *_mutable(),
        _tenant_id_unique("source_systems"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_source_systems_tenant_id_code"),
    )
    op.create_table(
        "source_authority_rules",
        _id(),
        _tenant(),
        sa.Column("source_system_id", sa.String(36), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("authority", sa.String(16), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        *_mutable(),
        _tenant_id_unique("source_authority_rules"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_system_id"],
            ["source_systems.tenant_id", "source_systems.id"],
        ),
        _interval(),
    )
    op.create_table(
        "source_observations",
        _id(),
        _tenant(),
        sa.Column("source_system_id", sa.String(36), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("source_record_key", sa.String(200), nullable=False),
        sa.Column("source_record_fingerprint", sa.String(64), nullable=False),
        sa.Column("source_record_version", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.String(32), nullable=False),
        sa.Column("mapping_version", sa.String(64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("semantic_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        _tenant_id_unique("source_observations"),
        sa.UniqueConstraint(
            "tenant_id",
            "source_system_id",
            "entity_type",
            "source_record_fingerprint",
            "source_record_version",
            name="uq_source_observations_source_version",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_system_id"],
            ["source_systems.tenant_id", "source_systems.id"],
        ),
    )
    op.create_table(
        "learner_lineage_links",
        _id(),
        _tenant(),
        sa.Column("source_observation_id", sa.String(36), nullable=False),
        sa.Column("learner_id", sa.String(36), nullable=False),
        sa.Column("relationship", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_observation_id"],
            ["source_observations.tenant_id", "source_observations.id"],
        ),
        sa.ForeignKeyConstraint(["tenant_id", "learner_id"], ["learners.tenant_id", "learners.id"]),
    )
    op.create_table(
        "reconciliation_issues",
        _id(),
        _tenant(foreign_key=True),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.String(36)),
        sa.Column("issue_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("resolution_code", sa.String(40)),
        sa.Column("resolved_by_user_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        *_mutable(),
        _tenant_id_unique("reconciliation_issues"),
    )
    op.create_table(
        "subject_rights_requests",
        _id(),
        _tenant(),
        sa.Column("learner_id", sa.String(36), nullable=False),
        sa.Column("request_type", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason_code", sa.String(40), nullable=False),
        sa.Column("disposition_code", sa.String(40)),
        sa.Column(
            "created_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        *_mutable(),
        _tenant_id_unique("subject_rights_requests"),
        sa.ForeignKeyConstraint(["tenant_id", "learner_id"], ["learners.tenant_id", "learners.id"]),
    )
    op.create_table(
        "subject_export_manifests",
        _id(),
        _tenant(foreign_key=True),
        sa.Column("learner_id", sa.String(36), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "request_id",
            name="uq_subject_export_manifests_request",
        ),
    )


def _seed_permissions() -> None:
    bind = op.get_bind()
    permission_table = sa.table(
        "permissions",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("requires_mfa", sa.Boolean),
        sa.column("requires_recent_auth", sa.Boolean),
    )
    role_table = sa.table("roles", sa.column("id", sa.String), sa.column("name", sa.String))
    role_permission_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.String),
        sa.column("permission_id", sa.String),
    )
    names = sorted(set().union(*PHASE3_ROLE_PERMISSIONS.values()))
    permission_ids: dict[str, str] = {}
    for name in names:
        existing = bind.execute(
            sa.select(permission_table.c.id).where(permission_table.c.name == name)
        ).scalar_one_or_none()
        permission_id = existing or str(uuid5(NAMESPACE_URL, f"education-erp:{name}"))
        permission_ids[name] = permission_id
        if existing is None:
            protected = name in {
                "learner_identifier:read",
                "lineage:read",
                "reconciliation:manage",
                "subject_rights:read",
                "subject_rights:manage",
                "subject_export:create",
            }
            bind.execute(
                permission_table.insert().values(
                    id=permission_id,
                    name=name,
                    description=name,
                    requires_mfa=protected,
                    requires_recent_auth=protected,
                )
            )
    for role_name, permission_names in PHASE3_ROLE_PERMISSIONS.items():
        role_id = bind.execute(
            sa.select(role_table.c.id).where(role_table.c.name == role_name)
        ).scalar_one()
        for name in permission_names:
            exists = bind.execute(
                sa.select(role_permission_table.c.role_id).where(
                    role_permission_table.c.role_id == role_id,
                    role_permission_table.c.permission_id == permission_ids[name],
                )
            ).scalar_one_or_none()
            if exists is None:
                bind.execute(
                    role_permission_table.insert().values(
                        role_id=role_id,
                        permission_id=permission_ids[name],
                    )
                )


def upgrade() -> None:
    bind = op.get_bind()
    _create_phase3_tables()
    for link_table, (target_table, target_column) in LINEAGE_TARGETS.items():
        op.create_table(
            link_table,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False),
            sa.Column("source_observation_id", sa.String(36), nullable=False),
            sa.Column(target_column, sa.String(36), nullable=False),
            sa.Column("relationship", sa.String(24), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["tenant_id", "source_observation_id"],
                ["source_observations.tenant_id", "source_observations.id"],
            ),
            sa.ForeignKeyConstraint(
                ["tenant_id", target_column],
                [f"{target_table}.tenant_id", f"{target_table}.id"],
            ),
        )
    _seed_permissions()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        op.execute(
            "ALTER TABLE programme_versions ADD CONSTRAINT "
            "ex_programme_versions_effective EXCLUDE USING gist "
            "(tenant_id WITH =, programme_id WITH =, "
            "daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[)') WITH &&)"
        )
        op.execute(
            "ALTER TABLE course_versions ADD CONSTRAINT "
            "ex_course_versions_effective EXCLUDE USING gist "
            "(tenant_id WITH =, course_id WITH =, "
            "daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[)') WITH &&)"
        )
        for enrolment_table, target_column in (
            ("programme_enrolments", "programme_version_id"),
            ("offering_enrolments", "offering_id"),
        ):
            op.execute(
                f'ALTER TABLE "{enrolment_table}" ADD CONSTRAINT '
                f'"ex_{enrolment_table}_effective" EXCLUDE USING gist '
                f"(tenant_id WITH =, learner_id WITH =, {target_column} WITH =, "
                "daterange(effective_from, COALESCE(effective_to, 'infinity'::date), "
                "'[)') WITH &&)"
            )
        op.execute(
            "CREATE FUNCTION phase3_reject_history_mutation() RETURNS trigger "
            "LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'phase 3 history is immutable'; END $$"
        )
        history_tables = (
            "source_observations",
            "learner_lineage_links",
            "enrolment_status_history",
            "subject_export_manifests",
            *LINEAGE_TARGETS,
        )
        for name in (*TABLES, *LINEAGE_TARGETS):
            op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
            op.execute(
                f'CREATE POLICY "{name}_tenant_isolation" ON "{name}" '
                "USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')) "
                "WITH CHECK (tenant_id = "
                "nullif(current_setting('app.tenant_id', true), ''))"
            )
            op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON "{name}" TO education_erp_app')
        for name in history_tables:
            op.execute(
                f'CREATE TRIGGER "{name}_immutable" BEFORE UPDATE OR DELETE ON "{name}" '
                "FOR EACH ROW EXECUTE FUNCTION phase3_reject_history_mutation()"
            )
            op.execute(f'REVOKE UPDATE, DELETE ON "{name}" FROM education_erp_app')


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for name in reversed((*TABLES, *LINEAGE_TARGETS)):
            op.execute(f'DROP POLICY IF EXISTS "{name}_tenant_isolation" ON "{name}"')
        op.execute("DROP FUNCTION IF EXISTS phase3_reject_history_mutation() CASCADE")
    for name in reversed(tuple(LINEAGE_TARGETS)):
        op.drop_table(name)
    for name in reversed(TABLES):
        op.drop_table(name)
    permission_table = sa.table(
        "permissions", sa.column("id", sa.String), sa.column("name", sa.String)
    )
    role_permission_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.String),
        sa.column("permission_id", sa.String),
    )
    permission_ids = sa.select(permission_table.c.id).where(
        permission_table.c.name.in_(sorted(set().union(*PHASE3_ROLE_PERMISSIONS.values())))
    )
    bind.execute(
        role_permission_table.delete().where(
            role_permission_table.c.permission_id.in_(permission_ids)
        )
    )
    bind.execute(
        permission_table.delete().where(
            permission_table.c.name.in_(sorted(set().union(*PHASE3_ROLE_PERMISSIONS.values())))
        )
    )
