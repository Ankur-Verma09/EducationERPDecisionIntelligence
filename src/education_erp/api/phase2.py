"""Phase 2 identity, institution, membership, role, and audit APIs."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from education_erp.access.policy import (
    CurrentUser,
    apply_tenant_context,
    is_platform_admin,
)
from education_erp.api.dependencies import (
    current_user,
    database_session,
    require_permission,
    tenant_context,
    token_principal,
)
from education_erp.api.phase2_controls import decode_cursor, encode_cursor, idempotent
from education_erp.errors import ApiError
from education_erp.identity.principal import TokenPrincipal
from education_erp.persistence.models import (
    AuditEvent,
    Campus,
    Department,
    ExternalIdentity,
    Institution,
    Membership,
    Role,
    RoleAssignment,
    TenantSecurityPolicy,
    User,
)

router = APIRouter(tags=["identity-and-tenancy"])
SessionDependency = Annotated[Session, Depends(database_session)]
PrincipalDependency = Annotated[TokenPrincipal, Depends(token_principal)]


class ExternalIdentityInput(BaseModel):
    issuer: str = Field(min_length=8, max_length=500)
    subject: str = Field(min_length=1, max_length=255)
    work_email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=160)


class InstitutionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=r"^[a-z][a-z0-9-]{2,79}$")
    legal_name: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)
    data_region: str = Field(min_length=2, max_length=80)
    initial_owner: ExternalIdentityInput


class InstitutionResponse(BaseModel):
    id: str
    slug: str
    legal_name: str
    display_name: str
    status: str
    data_region: str
    version: int


class MembershipCreate(ExternalIdentityInput):
    model_config = ConfigDict(extra="forbid")


class MembershipResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    status: str
    version: int


class RoleAssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    campus_id: str | None = None
    department_id: str | None = None
    expires_at: datetime | None = None


class MeResponse(BaseModel):
    id: str
    display_name: str
    work_email: str


def audit(
    session: Session,
    request: Request,
    *,
    tenant_id: str | None,
    actor_user_id: str | None,
    action: str,
    target_type: str,
    target_id: str | None,
    reason: str | None = None,
    changes: dict[str, object] | None = None,
) -> None:
    session.add(
        AuditEvent(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            outcome="success",
            request_id=request.state.request_id,
            reason=reason,
            changes=changes or {},
        )
    )


@router.get("/me", response_model=MeResponse)
def get_me(session: SessionDependency, principal: PrincipalDependency) -> MeResponse:
    user = current_user(session, principal)
    return MeResponse(id=user.id, display_name=user.display_name, work_email=user.work_email)


@router.get("/me/memberships")
def get_my_memberships(
    session: SessionDependency,
    principal: PrincipalDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> dict[str, object]:
    user = current_user(session, principal)
    after = decode_cursor(cursor)
    statement = select(Membership).where(
        Membership.user_id == user.id,
        Membership.status.in_({"active", "invited", "suspended"}),
    )
    if after:
        statement = statement.where(Membership.id > after)
    rows = list(session.scalars(statement.order_by(Membership.id).limit(limit + 1)))
    visible = rows[:limit]
    return {
        "items": [
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "status": row.status,
                "version": row.version,
            }
            for row in visible
        ],
        "next_cursor": encode_cursor(visible[-1].id) if len(rows) > limit else None,
    }


@router.post(
    "/platform/institutions",
    response_model=InstitutionResponse,
    status_code=201,
)
@idempotent
def create_institution(
    body: InstitutionCreate,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> InstitutionResponse:
    actor = current_user(session, principal)
    if not is_platform_admin(session, actor.id):
        raise ApiError(403, "permission_denied", "The operation is not permitted")
    if not principal.has_mfa(request.app.state.settings.privileged_mfa_methods):
        raise ApiError(403, "mfa_required", "Multi-factor authentication is required")
    if session.scalar(select(Institution.id).where(Institution.slug == body.slug)):
        raise ApiError(409, "state_conflict", "The institution slug is already in use")

    institution = Institution(
        slug=body.slug,
        legal_name=body.legal_name,
        display_name=body.display_name,
        data_region=body.data_region,
        status="pending",
    )
    session.add(institution)
    session.flush()
    apply_tenant_context(session, institution.id)

    owner = session.scalar(
        select(User)
        .join(ExternalIdentity, ExternalIdentity.user_id == User.id)
        .where(
            ExternalIdentity.issuer == body.initial_owner.issuer,
            ExternalIdentity.subject == body.initial_owner.subject,
        )
    )
    if owner is None:
        owner = User(
            display_name=body.initial_owner.display_name,
            work_email=body.initial_owner.work_email.lower(),
            status="active",
        )
        session.add(owner)
        session.flush()
        session.add(
            ExternalIdentity(
                user_id=owner.id,
                issuer=body.initial_owner.issuer.rstrip("/"),
                subject=body.initial_owner.subject,
            )
        )
    membership = Membership(
        tenant_id=institution.id,
        user_id=owner.id,
        status="active",
        invited_by_user_id=actor.id,
        activated_at=datetime.now(UTC),
    )
    session.add(membership)
    session.add(TenantSecurityPolicy(tenant_id=institution.id))
    session.flush()
    owner_role = session.scalar(select(Role).where(Role.name == "tenant_owner"))
    if owner_role is None:
        raise RuntimeError("built-in tenant_owner role is missing")
    session.add(
        RoleAssignment(
            tenant_id=institution.id,
            membership_id=membership.id,
            role_id=owner_role.id,
            granted_by_user_id=actor.id,
        )
    )
    audit(
        session,
        request,
        tenant_id=institution.id,
        actor_user_id=actor.id,
        action="institution.created",
        target_type="institution",
        target_id=institution.id,
    )
    session.flush()
    return InstitutionResponse.model_validate(institution, from_attributes=True)


def _tenant_actor(
    session: Session,
    principal: TokenPrincipal,
    tenant_id: str,
    permission: str,
) -> tuple[CurrentUser, str]:
    context = tenant_context(session, principal, tenant_id)
    require_permission(context, permission)
    return context.user, context.membership_id


@router.get("/tenants/{tenant_id}", response_model=InstitutionResponse)
def get_institution(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> InstitutionResponse:
    _tenant_actor(session, principal, tenant_id, "institution:read")
    institution = session.get(Institution, tenant_id)
    if institution is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return InstitutionResponse.model_validate(institution, from_attributes=True)


@router.get("/tenants/{tenant_id}/memberships/{membership_id}")
def get_membership(
    tenant_id: str,
    membership_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> MembershipResponse:
    _tenant_actor(session, principal, tenant_id, "membership:read")
    membership = session.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.id == membership_id,
        )
    )
    if membership is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return MembershipResponse.model_validate(membership, from_attributes=True)


@router.get("/tenants/{tenant_id}/memberships/{membership_id}/role-assignments")
def list_role_assignments(
    tenant_id: str,
    membership_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> list[dict[str, object]]:
    _tenant_actor(session, principal, tenant_id, "role:read")
    membership = session.scalar(
        select(Membership.id).where(
            Membership.tenant_id == tenant_id,
            Membership.id == membership_id,
        )
    )
    if membership is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    rows = session.execute(
        select(RoleAssignment, Role.name)
        .join(Role, Role.id == RoleAssignment.role_id)
        .where(
            RoleAssignment.tenant_id == tenant_id,
            RoleAssignment.membership_id == membership_id,
            RoleAssignment.revoked_at.is_(None),
        )
    )
    return [
        {
            "id": assignment.id,
            "role": role_name,
            "campus_id": assignment.campus_id,
            "department_id": assignment.department_id,
            "expires_at": assignment.expires_at,
            "version": assignment.version,
        }
        for assignment, role_name in rows
    ]


@router.post(
    "/tenants/{tenant_id}/memberships",
    response_model=MembershipResponse,
    status_code=201,
)
@idempotent
def create_membership(
    tenant_id: str,
    body: MembershipCreate,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> MembershipResponse:
    actor, _ = _tenant_actor(session, principal, tenant_id, "membership:invite")
    identity = session.scalar(
        select(ExternalIdentity).where(
            ExternalIdentity.issuer == body.issuer.rstrip("/"),
            ExternalIdentity.subject == body.subject,
        )
    )
    if identity is None:
        user = User(
            display_name=body.display_name,
            work_email=body.work_email.lower(),
            status="active",
        )
        session.add(user)
        session.flush()
        session.add(
            ExternalIdentity(
                user_id=user.id,
                issuer=body.issuer.rstrip("/"),
                subject=body.subject,
            )
        )
    else:
        loaded_user = session.get(User, identity.user_id)
        if loaded_user is None:
            raise RuntimeError("external identity references a missing user")
        user = loaded_user
    existing = session.scalar(
        select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.user_id == user.id,
        )
    )
    if existing is not None:
        raise ApiError(409, "state_conflict", "A membership already exists")
    membership = Membership(
        tenant_id=tenant_id,
        user_id=user.id,
        status="active",
        invited_by_user_id=actor.id,
        activated_at=datetime.now(UTC),
    )
    session.add(membership)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="membership.created",
        target_type="membership",
        target_id=membership.id,
    )
    return MembershipResponse.model_validate(membership, from_attributes=True)


@router.post(
    "/tenants/{tenant_id}/memberships/{membership_id}/role-assignments",
    status_code=201,
)
@idempotent
def assign_role(
    tenant_id: str,
    membership_id: str,
    body: RoleAssignmentCreate,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor, actor_membership_id = _tenant_actor(session, principal, tenant_id, "role:assign")
    if body.role == "tenant_owner":
        context = tenant_context(session, principal, tenant_id)
        role_names = set(
            session.scalars(
                select(Role.name)
                .join(RoleAssignment, RoleAssignment.role_id == Role.id)
                .where(
                    RoleAssignment.membership_id == context.membership_id,
                    RoleAssignment.revoked_at.is_(None),
                )
            )
        )
        if "tenant_owner" not in role_names:
            raise ApiError(403, "permission_denied", "Only tenant owners may grant ownership")
    membership = session.scalar(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.tenant_id == tenant_id,
            Membership.status == "active",
        )
    )
    role = session.scalar(select(Role).where(Role.name == body.role))
    if membership is None or role is None or body.role == "platform_admin":
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    campus = None
    department = None
    if body.campus_id:
        campus = session.scalar(
            select(Campus).where(Campus.tenant_id == tenant_id, Campus.id == body.campus_id)
        )
        if campus is None:
            raise ApiError(404, "resource_not_found", "The requested resource was not found")
    if body.department_id:
        department = session.scalar(
            select(Department).where(
                Department.tenant_id == tenant_id,
                Department.id == body.department_id,
            )
        )
        if department is None or (body.campus_id and department.campus_id != body.campus_id):
            raise ApiError(404, "resource_not_found", "The requested resource was not found")
    actor_assignments = list(
        session.execute(
            select(Role.name, RoleAssignment.campus_id, RoleAssignment.department_id)
            .join(Role, Role.id == RoleAssignment.role_id)
            .where(
                RoleAssignment.membership_id == actor_membership_id,
                RoleAssignment.revoked_at.is_(None),
            )
        )
    )
    actor_roles = {name for name, _, _ in actor_assignments}
    if not actor_roles.intersection({"tenant_owner", "tenant_admin"}):
        delegated = any(
            name == "department_admin"
            and department_id is not None
            and department_id == body.department_id
            and (campus_id is None or campus_id == body.campus_id)
            for name, campus_id, department_id in actor_assignments
        )
        if body.role not in {"department_admin", "viewer"} or not delegated:
            raise ApiError(403, "delegation_exceeded", "The requested delegation exceeds scope")
    assignment = RoleAssignment(
        tenant_id=tenant_id,
        membership_id=membership.id,
        role_id=role.id,
        campus_id=body.campus_id,
        department_id=body.department_id,
        expires_at=body.expires_at,
        granted_by_user_id=actor.id,
    )
    session.add(assignment)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="role.assigned",
        target_type="role_assignment",
        target_id=assignment.id,
        changes={"role": body.role},
    )
    return {"id": assignment.id, "version": assignment.version}


@router.get("/tenants/{tenant_id}/audit-events")
def list_audit_events(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "audit:read")
    if not principal.has_mfa(request.app.state.settings.privileged_mfa_methods):
        raise ApiError(403, "mfa_required", "Multi-factor authentication is required")
    after = decode_cursor(cursor)
    statement = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id)
    if after:
        statement = statement.where(AuditEvent.id > after)
    events = list(session.scalars(statement.order_by(AuditEvent.id).limit(limit + 1)))
    visible = events[:limit]
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="audit.accessed",
        target_type="audit_event_collection",
        target_id=None,
    )
    return {
        "items": [
            {
                "id": event.id,
                "action": event.action,
                "target_type": event.target_type,
                "target_id": event.target_id,
                "outcome": event.outcome,
                "request_id": event.request_id,
                "occurred_at": event.occurred_at,
            }
            for event in visible
        ],
        "next_cursor": encode_cursor(visible[-1].id) if len(events) > limit else None,
    }
