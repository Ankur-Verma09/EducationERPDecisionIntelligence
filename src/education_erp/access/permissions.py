"""Canonical built-in Phase 2 roles and permissions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from education_erp.persistence.models import Permission, Role, RolePermission

PERMISSIONS = frozenset(
    {
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
        "connector:read",
        "connector:manage",
        "connector:run",
        "connector:reconcile",
        "connector:replay",
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "platform_admin": frozenset(
        {
            "institution:create",
            "institution:read",
            "institution:suspend",
            "institution:activate",
        }
    ),
    "tenant_owner": PERMISSIONS - {"institution:create"},
    "tenant_admin": PERMISSIONS
    - {
        "institution:create",
        "institution:suspend",
        "institution:activate",
        "support_access:approve",
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
        "connector:read",
        "connector:manage",
        "connector:run",
        "connector:reconcile",
        "connector:replay",
    },
    "security_admin": frozenset(
        {
            "institution:read",
            "membership:read",
            "membership:update",
            "membership:revoke",
            "role:read",
            "security_policy:read",
            "security_policy:update",
            "audit:read",
        }
    ),
    "auditor": frozenset(
        {
            "institution:read",
            "campus:read",
            "department:read",
            "membership:read",
            "role:read",
            "security_policy:read",
            "audit:read",
            "academic_structure:read",
            "learner:read",
            "enrolment:read",
            "lineage:read",
            "connector:read",
        }
    ),
    "registrar": frozenset(
        {
            "institution:read",
            "campus:read",
            "department:read",
            "membership:read",
            "role:read",
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
            "connector:read",
            "connector:run",
            "connector:reconcile",
            "connector:replay",
        }
    ),
    "department_admin": frozenset(
        {
            "institution:read",
            "campus:read",
            "department:read",
            "membership:invite",
            "membership:read",
            "membership:update",
            "role:read",
            "role:assign",
            "role:revoke",
            "academic_structure:read",
            "academic_structure:manage",
            "learner:read",
            "enrolment:read",
            "enrolment:manage",
        }
    ),
    "viewer": frozenset(
        {
            "institution:read",
            "campus:read",
            "department:read",
            "academic_structure:read",
        }
    ),
}


def seed_builtin_access(session: Session) -> None:
    """Idempotently seed built-in access definitions for tests and bootstrap."""

    if session.scalar(select(Role.id).limit(1)) is not None:
        return
    permissions: dict[str, Permission] = {}
    for name in sorted(PERMISSIONS):
        permission = Permission(
            name=name,
            description=name,
            requires_mfa=name
            in {
                "institution:suspend",
                "institution:activate",
                "membership:revoke",
                "role:assign",
                "role:revoke",
                "security_policy:update",
                "audit:read",
                "support_access:approve",
                "learner_identifier:read",
                "lineage:read",
                "connector:read",
                "reconciliation:manage",
                "subject_rights:read",
                "subject_rights:manage",
                "subject_export:create",
            },
            requires_recent_auth=name
            in {
                "institution:suspend",
                "institution:activate",
                "role:assign",
                "role:revoke",
                "security_policy:update",
                "support_access:approve",
            },
        )
        permissions[name] = permission
        session.add(permission)
    session.flush()
    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = Role(
            name=role_name,
            description=f"Built-in {role_name.replace('_', ' ')} role",
            is_builtin=True,
        )
        session.add(role)
        session.flush()
        session.add_all(
            [
                RolePermission(role_id=role.id, permission_id=permissions[name].id)
                for name in permission_names
            ]
        )
