"""Add Phase 2 identity, institution, RBAC, audit, and tenant RLS.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-29
"""

from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None

TENANT_TABLES = (
    "campuses",
    "departments",
    "memberships",
    "role_assignments",
    "tenant_security_policies",
    "audit_events",
)

ROLE_NAMES = (
    "platform_admin",
    "tenant_owner",
    "tenant_admin",
    "security_admin",
    "auditor",
    "registrar",
    "department_admin",
    "viewer",
)
PERMISSION_NAMES = (
    "institution:create",
    "institution:read",
    "institution:update",
    "institution:suspend",
    "institution:activate",
    "campus:create",
    "campus:read",
    "campus:update",
    "department:create",
    "department:read",
    "department:update",
    "membership:invite",
    "membership:read",
    "membership:update",
    "membership:revoke",
    "role:read",
    "role:assign",
    "role:revoke",
    "security_policy:read",
    "security_policy:update",
    "audit:read",
    "support_access:approve",
)


def _timestamps() -> list[sa.Column[Any]]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("legal_name", sa.String(200), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("data_region", sa.String(80), nullable=False),
        sa.Column("security_epoch", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("work_email", sa.String(320), nullable=False),
        sa.Column("security_epoch", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "external_identities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("issuer", sa.String(500), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("issuer", "subject", name="uq_external_identities_issuer_subject"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("requires_mfa", sa.Boolean(), nullable=False),
        sa.Column("requires_recent_auth", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id"), primary_key=True),
        sa.Column(
            "permission_id",
            sa.String(36),
            sa.ForeignKey("permissions.id"),
            primary_key=True,
        ),
    )
    role_ids = {
        name: f"00000000-0000-0000-0001-{index:012d}" for index, name in enumerate(ROLE_NAMES, 1)
    }
    permission_ids = {
        name: f"00000000-0000-0000-0002-{index:012d}"
        for index, name in enumerate(PERMISSION_NAMES, 1)
    }
    op.bulk_insert(
        sa.table(
            "roles",
            sa.column("id", sa.String),
            sa.column("name", sa.String),
            sa.column("description", sa.String),
            sa.column("is_builtin", sa.Boolean),
        ),
        [
            {
                "id": role_ids[name],
                "name": name,
                "description": f"Built-in {name.replace('_', ' ')} role",
                "is_builtin": True,
            }
            for name in ROLE_NAMES
        ],
    )
    op.create_table(
        "platform_role_assignments",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role_name", sa.String(80), primary_key=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.bulk_insert(
        sa.table(
            "permissions",
            sa.column("id", sa.String),
            sa.column("name", sa.String),
            sa.column("description", sa.String),
            sa.column("requires_mfa", sa.Boolean),
            sa.column("requires_recent_auth", sa.Boolean),
        ),
        [
            {
                "id": permission_ids[name],
                "name": name,
                "description": name,
                "requires_mfa": name
                in {
                    "institution:create",
                    "institution:suspend",
                    "institution:activate",
                    "membership:revoke",
                    "role:assign",
                    "role:revoke",
                    "security_policy:update",
                    "audit:read",
                    "support_access:approve",
                },
                "requires_recent_auth": name
                in {
                    "institution:suspend",
                    "institution:activate",
                    "role:assign",
                    "role:revoke",
                    "security_policy:update",
                    "support_access:approve",
                },
            }
            for name in PERMISSION_NAMES
        ],
    )
    role_permissions = {
        "platform_admin": {
            "institution:create",
            "institution:read",
            "institution:suspend",
            "institution:activate",
        },
        "tenant_owner": set(PERMISSION_NAMES) - {"institution:create"},
        "tenant_admin": {
            name
            for name in PERMISSION_NAMES
            if name
            not in {
                "institution:create",
                "institution:suspend",
                "institution:activate",
                "support_access:approve",
            }
        },
        "security_admin": {
            "institution:read",
            "membership:read",
            "membership:update",
            "membership:revoke",
            "role:read",
            "security_policy:read",
            "security_policy:update",
            "audit:read",
        },
        "auditor": {
            "institution:read",
            "campus:read",
            "department:read",
            "membership:read",
            "role:read",
            "security_policy:read",
            "audit:read",
        },
        "registrar": {
            "institution:read",
            "campus:read",
            "department:read",
            "membership:read",
            "role:read",
        },
        "department_admin": {
            "institution:read",
            "campus:read",
            "department:read",
            "membership:invite",
            "membership:read",
            "membership:update",
            "role:read",
            "role:assign",
            "role:revoke",
        },
        "viewer": {
            "institution:read",
            "campus:read",
            "department:read",
        },
    }
    op.bulk_insert(
        sa.table(
            "role_permissions",
            sa.column("role_id", sa.String),
            sa.column("permission_id", sa.String),
        ),
        [
            {
                "role_id": role_ids[role_name],
                "permission_id": permission_ids[permission_name],
            }
            for role_name, names in role_permissions.items()
            for permission_name in sorted(names)
        ],
    )
    op.create_table(
        "campuses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_campuses_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_campuses_tenant_id_code"),
    )
    op.create_table(
        "departments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("campus_id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "campus_id"], ["campuses.tenant_id", "campuses.id"]),
        sa.UniqueConstraint(
            "tenant_id",
            "campus_id",
            "code",
            name="uq_departments_tenant_id_campus_id_code",
        ),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("security_epoch", sa.Integer(), nullable=False),
        sa.Column("invited_by_user_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_id_user_id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_memberships_tenant_id_id"),
    )
    op.create_table(
        "role_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("membership_id", sa.String(36), nullable=False),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("campus_id", sa.String(36)),
        sa.Column("department_id", sa.String(36)),
        sa.Column("granted_by_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "membership_id",
            "role_id",
            "campus_id",
            "department_id",
            name="uq_active_role_assignment",
        ),
    )
    op.create_table(
        "tenant_security_policies",
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("institutions.id"),
            primary_key=True,
        ),
        sa.Column("mfa_required_for_all", sa.Boolean(), nullable=False),
        sa.Column("session_max_minutes", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.String(36)),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("target_type", sa.String(80), nullable=False),
        sa.Column("target_id", sa.String(36)),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("changes", sa.JSON(), nullable=False),
    )

    if op.get_bind().dialect.name == "postgresql":
        for table in TENANT_TABLES:
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(
                f'CREATE POLICY "{table}_tenant_isolation" ON "{table}" '
                "USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')) "
                "WITH CHECK (tenant_id = "
                "nullif(current_setting('app.tenant_id', true), ''))"
            )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table in reversed(TENANT_TABLES):
            op.execute(f'DROP POLICY IF EXISTS "{table}_tenant_isolation" ON "{table}"')
    for table in (
        "audit_events",
        "tenant_security_policies",
        "role_assignments",
        "memberships",
        "departments",
        "campuses",
        "role_permissions",
        "platform_role_assignments",
        "permissions",
        "roles",
        "external_identities",
        "users",
        "institutions",
    ):
        op.drop_table(table)
