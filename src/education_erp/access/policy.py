"""Deny-by-default tenant permission resolution."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Select, select, text
from sqlalchemy.orm import Session

from education_erp.identity.principal import TokenPrincipal
from education_erp.persistence.models import (
    ExternalIdentity,
    Institution,
    Membership,
    Permission,
    PlatformRoleAssignment,
    RoleAssignment,
    RolePermission,
    User,
)


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: str
    display_name: str
    work_email: str


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: str
    membership_id: str
    user: CurrentUser
    permissions: frozenset[str]
    assurance_methods: frozenset[str]
    permission_scopes: tuple[tuple[str, str | None, str | None], ...] = ()

    def permits(self, permission: str) -> bool:
        return permission in self.permissions

    def permits_scope(
        self,
        permission: str,
        campus_id: str | None = None,
        department_id: str | None = None,
    ) -> bool:
        if permission not in self.permissions:
            return False
        for name, assigned_campus, assigned_department in self.permission_scopes:
            if name != permission:
                continue
            if assigned_campus is None and assigned_department is None:
                return True
            if assigned_department is not None:
                if department_id == assigned_department:
                    return True
                continue
            if assigned_campus == campus_id:
                return True
        return False


def apply_tenant_context(session: Session, tenant_id: str) -> None:
    """Constrain the current transaction to one tenant on PostgreSQL."""

    if session.get_bind().dialect.name == "postgresql":
        session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )


def resolve_user(session: Session, principal: TokenPrincipal) -> CurrentUser | None:
    statement: Select[tuple[User]] = (
        select(User)
        .join(ExternalIdentity, ExternalIdentity.user_id == User.id)
        .where(
            ExternalIdentity.issuer == principal.issuer,
            ExternalIdentity.subject == principal.subject,
            User.status == "active",
        )
    )
    user = session.scalar(statement)
    if user is None:
        return None
    return CurrentUser(id=user.id, display_name=user.display_name, work_email=user.work_email)


def is_platform_admin(session: Session, user_id: str) -> bool:
    return (
        session.scalar(
            select(PlatformRoleAssignment.user_id).where(
                PlatformRoleAssignment.user_id == user_id,
                PlatformRoleAssignment.role_name == "platform_admin",
            )
        )
        is not None
    )


def resolve_tenant_context(
    session: Session,
    principal: TokenPrincipal,
    tenant_id: str,
) -> TenantContext | None:
    apply_tenant_context(session, tenant_id)
    user = resolve_user(session, principal)
    if user is None:
        return None
    institution_active = session.scalar(
        select(Institution.id).where(
            Institution.id == tenant_id,
            Institution.status == "active",
        )
    )
    if institution_active is None:
        return None
    membership = session.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.user_id == user.id,
            Membership.status == "active",
        )
    )
    if membership is None:
        return None
    if principal.issued_at < datetime.fromtimestamp(membership.security_epoch, UTC):
        return None
    permission_rows = tuple(
        session.execute(
            select(Permission.name, RoleAssignment.campus_id, RoleAssignment.department_id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(RoleAssignment, RoleAssignment.role_id == RolePermission.role_id)
            .where(
                RoleAssignment.tenant_id == tenant_id,
                RoleAssignment.membership_id == membership.id,
                RoleAssignment.revoked_at.is_(None),
                (
                    RoleAssignment.expires_at.is_(None)
                    | (RoleAssignment.expires_at > datetime.now(UTC))
                ),
            )
        ).tuples()
    )
    permissions = frozenset(row[0] for row in permission_rows)
    return TenantContext(
        tenant_id=tenant_id,
        membership_id=membership.id,
        user=user,
        permissions=permissions,
        assurance_methods=principal.assurance_methods,
        permission_scopes=permission_rows,
    )
