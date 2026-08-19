"""Remaining approved Phase 2 administration APIs."""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from education_erp.access.policy import apply_tenant_context, is_platform_admin
from education_erp.api.dependencies import current_user, database_session, token_principal
from education_erp.api.phase2 import _tenant_actor, audit
from education_erp.api.phase2_controls import decode_cursor, encode_cursor, idempotent
from education_erp.errors import ApiError
from education_erp.identity.principal import TokenPrincipal
from education_erp.persistence.models import (
    Campus,
    Department,
    Institution,
    Membership,
    Role,
    RoleAssignment,
    SupportAccessGrant,
    TenantSecurityPolicy,
)

router = APIRouter(tags=["identity-and-tenancy"])
SessionDependency = Annotated[Session, Depends(database_session)]
PrincipalDependency = Annotated[TokenPrincipal, Depends(token_principal)]


class HierarchyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(pattern=r"^[A-Z0-9_-]{1,40}$")
    name: str = Field(min_length=1, max_length=160)


class DepartmentCreate(HierarchyCreate):
    campus_id: str


class HierarchyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=160)
    status: Literal["active", "inactive"] | None = None


class InstitutionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    legal_name: str | None = Field(default=None, min_length=1, max_length=200)
    display_name: str | None = Field(default=None, min_length=1, max_length=200)


class ReasonInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=3, max_length=500)


class DeletionRequest(ReasonInput):
    tenant_owner_approval_membership_id: str


class SecurityPolicyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mfa_required_for_all: bool | None = None
    session_max_minutes: int | None = Field(default=None, ge=15, le=480)


class SupportGrantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    support_user_id: str
    reason: str = Field(min_length=3, max_length=1000)
    ticket_reference: str = Field(min_length=1, max_length=120)
    scope: dict[str, object] = Field(default_factory=dict)
    duration_minutes: int = Field(ge=5, le=240)


def _require_mfa(request: Request, principal: TokenPrincipal) -> None:
    if not principal.has_mfa(request.app.state.settings.privileged_mfa_methods):
        raise ApiError(403, "mfa_required", "Multi-factor authentication is required")


def _require_version(if_match: str | None, version: int) -> None:
    if if_match is None:
        raise ApiError(428, "precondition_required", "If-Match is required")
    if if_match.strip('"') != str(version):
        raise ApiError(412, "precondition_failed", "The resource version is stale")


def _etag(response: Response, version: int) -> None:
    response.headers["ETag"] = f'"{version}"'


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _hierarchy_dict(item: Campus | Department) -> dict[str, object]:
    result: dict[str, object] = {
        "id": item.id,
        "tenant_id": item.tenant_id,
        "code": item.code,
        "name": item.name,
        "status": item.status,
        "version": item.version,
    }
    if isinstance(item, Department):
        result["campus_id"] = item.campus_id
    return result


def _collection(
    rows: Sequence[Campus | Department | Institution | Membership],
    limit: int,
    serializer: object,
) -> dict[str, object]:
    visible = rows[:limit]
    render = cast(Callable[[object], dict[str, object]], serializer)
    return {
        "items": [render(item) for item in visible],
        "next_cursor": encode_cursor(visible[-1].id) if len(rows) > limit else None,
    }


@router.get("/platform/institutions")
def list_platform_institutions(
    session: SessionDependency,
    principal: PrincipalDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> dict[str, object]:
    actor = current_user(session, principal)
    if not is_platform_admin(session, actor.id):
        raise ApiError(403, "permission_denied", "The operation is not permitted")
    after = decode_cursor(cursor)
    statement = select(Institution)
    if after:
        statement = statement.where(Institution.id > after)
    rows = list(session.scalars(statement.order_by(Institution.id).limit(limit + 1)))
    return _collection(
        rows,
        limit,
        lambda row: {
            "id": row.id,
            "slug": row.slug,
            "display_name": row.display_name,
            "status": row.status,
            "data_region": row.data_region,
            "version": row.version,
        },
    )


@router.get("/platform/institutions/{tenant_id}")
def get_platform_institution(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor = current_user(session, principal)
    if not is_platform_admin(session, actor.id):
        raise ApiError(403, "permission_denied", "The operation is not permitted")
    institution = session.get(Institution, tenant_id)
    if institution is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return {
        "id": institution.id,
        "slug": institution.slug,
        "legal_name": institution.legal_name,
        "display_name": institution.display_name,
        "status": institution.status,
        "data_region": institution.data_region,
        "version": institution.version,
    }


@router.post("/platform/institutions/{tenant_id}/activate")
@idempotent
def activate_institution(
    tenant_id: str,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor = current_user(session, principal)
    if not is_platform_admin(session, actor.id):
        raise ApiError(403, "permission_denied", "The operation is not permitted")
    _require_mfa(request, principal)
    apply_tenant_context(session, tenant_id)
    institution = session.get(Institution, tenant_id)
    policy = session.get(TenantSecurityPolicy, tenant_id)
    if institution is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    if policy is None or institution.status not in {"pending", "suspended"}:
        raise ApiError(409, "state_conflict", "The institution cannot be activated")
    institution.status = "active"
    institution.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="institution.activated",
        target_type="institution",
        target_id=tenant_id,
    )
    return {"id": tenant_id, "status": institution.status, "version": institution.version}


@router.post("/platform/institutions/{tenant_id}/suspend")
@idempotent
def suspend_institution(
    tenant_id: str,
    body: ReasonInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor = current_user(session, principal)
    if not is_platform_admin(session, actor.id):
        raise ApiError(403, "permission_denied", "The operation is not permitted")
    _require_mfa(request, principal)
    apply_tenant_context(session, tenant_id)
    institution = session.get(Institution, tenant_id)
    if institution is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    if institution.status != "active":
        raise ApiError(409, "state_conflict", "The institution is not active")
    institution.status = "suspended"
    institution.security_epoch += 1
    institution.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="institution.suspended",
        target_type="institution",
        target_id=tenant_id,
        changes={"reason": body.reason},
    )
    return {"id": tenant_id, "status": institution.status, "version": institution.version}


@router.post("/platform/institutions/{tenant_id}/request-deletion")
@idempotent
def request_institution_deletion(
    tenant_id: str,
    body: DeletionRequest,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor = current_user(session, principal)
    if not is_platform_admin(session, actor.id):
        raise ApiError(403, "permission_denied", "The operation is not permitted")
    _require_mfa(request, principal)
    apply_tenant_context(session, tenant_id)
    institution = session.get(Institution, tenant_id)
    if institution is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    owner_role_id = session.scalar(select(Role.id).where(Role.name == "tenant_owner"))
    approval = session.scalar(
        select(RoleAssignment.id)
        .join(Membership, Membership.id == RoleAssignment.membership_id)
        .where(
            RoleAssignment.tenant_id == tenant_id,
            RoleAssignment.membership_id == body.tenant_owner_approval_membership_id,
            RoleAssignment.role_id == owner_role_id,
            RoleAssignment.revoked_at.is_(None),
            Membership.status == "active",
        )
    )
    if approval is None:
        raise ApiError(403, "owner_approval_required", "Active tenant-owner approval is required")
    if institution.deletion_requested_at is not None:
        raise ApiError(409, "state_conflict", "Deletion has already been requested")
    institution.deletion_requested_at = datetime.now(UTC)
    institution.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="institution.deletion_requested",
        target_type="institution",
        target_id=tenant_id,
        changes={
            "reason": body.reason,
            "tenant_owner_approval_membership_id": body.tenant_owner_approval_membership_id,
        },
    )
    return {
        "id": tenant_id,
        "status": "deletion_requested",
        "deletion_requested_at": institution.deletion_requested_at,
        "version": institution.version,
    }


@router.patch("/tenants/{tenant_id}")
@idempotent
def update_institution(
    tenant_id: str,
    body: InstitutionUpdate,
    response: Response,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "institution:update")
    institution = session.get(Institution, tenant_id)
    if institution is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _require_version(if_match, institution.version)
    for name, value in body.model_dump(exclude_none=True).items():
        setattr(institution, name, value)
    institution.version += 1
    _etag(response, institution.version)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="institution.updated",
        target_type="institution",
        target_id=tenant_id,
        changes=body.model_dump(exclude_none=True),
    )
    return {
        "id": institution.id,
        "display_name": institution.display_name,
        "legal_name": institution.legal_name,
        "version": institution.version,
    }


@router.get("/tenants/{tenant_id}/campuses")
def list_campuses(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> dict[str, object]:
    _tenant_actor(session, principal, tenant_id, "campus:read")
    after = decode_cursor(cursor)
    statement = select(Campus).where(Campus.tenant_id == tenant_id)
    if after:
        statement = statement.where(Campus.id > after)
    rows = list(session.scalars(statement.order_by(Campus.id).limit(limit + 1)))
    return _collection(rows, limit, _hierarchy_dict)


@router.post("/tenants/{tenant_id}/campuses", status_code=201)
@idempotent
def create_campus(
    tenant_id: str,
    body: HierarchyCreate,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "campus:create")
    if session.scalar(
        select(Campus.id).where(Campus.tenant_id == tenant_id, Campus.code == body.code)
    ):
        raise ApiError(409, "state_conflict", "The campus code is already in use")
    campus = Campus(tenant_id=tenant_id, code=body.code, name=body.name)
    session.add(campus)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="campus.created",
        target_type="campus",
        target_id=campus.id,
    )
    return _hierarchy_dict(campus)


@router.get("/tenants/{tenant_id}/campuses/{campus_id}")
def get_campus(
    tenant_id: str,
    campus_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _tenant_actor(session, principal, tenant_id, "campus:read")
    campus = session.scalar(
        select(Campus).where(Campus.tenant_id == tenant_id, Campus.id == campus_id)
    )
    if campus is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return _hierarchy_dict(campus)


@router.patch("/tenants/{tenant_id}/campuses/{campus_id}")
@idempotent
def update_campus(
    tenant_id: str,
    campus_id: str,
    body: HierarchyUpdate,
    response: Response,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "campus:update")
    campus = session.scalar(
        select(Campus).where(Campus.tenant_id == tenant_id, Campus.id == campus_id)
    )
    if campus is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _require_version(if_match, campus.version)
    for name, value in body.model_dump(exclude_none=True).items():
        setattr(campus, name, value)
    campus.version += 1
    _etag(response, campus.version)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="campus.updated",
        target_type="campus",
        target_id=campus.id,
    )
    return _hierarchy_dict(campus)


@router.get("/tenants/{tenant_id}/departments")
def list_departments(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    campus_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> dict[str, object]:
    _tenant_actor(session, principal, tenant_id, "department:read")
    statement = select(Department).where(Department.tenant_id == tenant_id)
    if campus_id:
        statement = statement.where(Department.campus_id == campus_id)
    after = decode_cursor(cursor)
    if after:
        statement = statement.where(Department.id > after)
    rows = list(session.scalars(statement.order_by(Department.id).limit(limit + 1)))
    return _collection(rows, limit, _hierarchy_dict)


@router.post("/tenants/{tenant_id}/departments", status_code=201)
@idempotent
def create_department(
    tenant_id: str,
    body: DepartmentCreate,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "department:create")
    campus = session.scalar(
        select(Campus.id).where(Campus.tenant_id == tenant_id, Campus.id == body.campus_id)
    )
    if campus is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    department = Department(
        tenant_id=tenant_id,
        campus_id=body.campus_id,
        code=body.code,
        name=body.name,
    )
    session.add(department)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="department.created",
        target_type="department",
        target_id=department.id,
    )
    return _hierarchy_dict(department)


@router.get("/tenants/{tenant_id}/departments/{department_id}")
def get_department(
    tenant_id: str,
    department_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _tenant_actor(session, principal, tenant_id, "department:read")
    department = session.scalar(
        select(Department).where(
            Department.tenant_id == tenant_id,
            Department.id == department_id,
        )
    )
    if department is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return _hierarchy_dict(department)


@router.patch("/tenants/{tenant_id}/departments/{department_id}")
@idempotent
def update_department(
    tenant_id: str,
    department_id: str,
    body: HierarchyUpdate,
    response: Response,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "department:update")
    department = session.scalar(
        select(Department).where(
            Department.tenant_id == tenant_id,
            Department.id == department_id,
        )
    )
    if department is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _require_version(if_match, department.version)
    for name, value in body.model_dump(exclude_none=True).items():
        setattr(department, name, value)
    department.version += 1
    _etag(response, department.version)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="department.updated",
        target_type="department",
        target_id=department.id,
    )
    return _hierarchy_dict(department)


@router.get("/tenants/{tenant_id}/memberships")
def list_memberships(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
    state: str | None = None,
) -> dict[str, object]:
    _tenant_actor(session, principal, tenant_id, "membership:read")
    statement = select(Membership).where(Membership.tenant_id == tenant_id)
    if state:
        statement = statement.where(Membership.status == state)
    after = decode_cursor(cursor)
    if after:
        statement = statement.where(Membership.id > after)
    rows = list(session.scalars(statement.order_by(Membership.id).limit(limit + 1)))
    return _collection(
        rows,
        limit,
        lambda row: {
            "id": row.id,
            "user_id": row.user_id,
            "status": row.status,
            "version": row.version,
        },
    )


@router.post("/tenants/{tenant_id}/memberships/{membership_id}/{action}")
@idempotent
def transition_membership(
    tenant_id: str,
    membership_id: str,
    action: Literal["activate", "suspend", "revoke"],
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    permission = "membership:revoke" if action == "revoke" else "membership:update"
    actor, _ = _tenant_actor(session, principal, tenant_id, permission)
    membership = session.scalar(
        select(Membership).where(Membership.tenant_id == tenant_id, Membership.id == membership_id)
    )
    if membership is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    transitions = {
        "activate": ({"invited", "suspended"}, "active"),
        "suspend": ({"active"}, "suspended"),
        "revoke": ({"active", "invited", "suspended"}, "revoked"),
    }
    allowed, target = transitions[action]
    if membership.status not in allowed:
        raise ApiError(409, "state_conflict", "The membership transition is invalid")
    if action in {"suspend", "revoke"}:
        owner_role = session.scalar(select(Role.id).where(Role.name == "tenant_owner"))
        is_owner = session.scalar(
            select(RoleAssignment.id).where(
                RoleAssignment.tenant_id == tenant_id,
                RoleAssignment.membership_id == membership_id,
                RoleAssignment.role_id == owner_role,
                RoleAssignment.revoked_at.is_(None),
            )
        )
        if is_owner:
            owner_count = session.scalar(
                select(func.count())
                .select_from(RoleAssignment)
                .join(Membership, Membership.id == RoleAssignment.membership_id)
                .where(
                    RoleAssignment.tenant_id == tenant_id,
                    RoleAssignment.role_id == owner_role,
                    RoleAssignment.revoked_at.is_(None),
                    Membership.status == "active",
                )
            )
            if owner_count == 1:
                raise ApiError(409, "last_owner", "The last tenant owner cannot be removed")
        _require_mfa(request, principal)
    membership.status = target
    membership.security_epoch += 1
    membership.version += 1
    now = datetime.now(UTC)
    if action == "activate":
        membership.activated_at = now
    if action == "revoke":
        membership.revoked_at = now
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action=f"membership.{action}d",
        target_type="membership",
        target_id=membership.id,
    )
    return {"id": membership.id, "status": membership.status, "version": membership.version}


@router.get("/tenants/{tenant_id}/roles")
def list_roles(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> list[dict[str, str]]:
    _tenant_actor(session, principal, tenant_id, "role:read")
    return [
        {"id": role.id, "name": role.name, "description": role.description}
        for role in session.scalars(
            select(Role).where(Role.name != "platform_admin").order_by(Role.name)
        )
    ]


@router.delete(
    "/tenants/{tenant_id}/memberships/{membership_id}/role-assignments/{assignment_id}",
    status_code=204,
)
@idempotent
def revoke_role(
    tenant_id: str,
    membership_id: str,
    assignment_id: str,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header()] = None,
) -> Response:
    actor, _ = _tenant_actor(session, principal, tenant_id, "role:revoke")
    _require_mfa(request, principal)
    assignment = session.scalar(
        select(RoleAssignment).where(
            RoleAssignment.tenant_id == tenant_id,
            RoleAssignment.membership_id == membership_id,
            RoleAssignment.id == assignment_id,
            RoleAssignment.revoked_at.is_(None),
        )
    )
    if assignment is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _require_version(if_match, assignment.version)
    role_name = session.scalar(select(Role.name).where(Role.id == assignment.role_id))
    if role_name == "tenant_owner":
        other_owner = session.scalar(
            select(RoleAssignment.id)
            .join(Role, Role.id == RoleAssignment.role_id)
            .where(
                RoleAssignment.tenant_id == tenant_id,
                RoleAssignment.id != assignment.id,
                RoleAssignment.revoked_at.is_(None),
                Role.name == "tenant_owner",
            )
        )
        if other_owner is None:
            raise ApiError(409, "last_owner", "The last tenant owner cannot be removed")
    assignment.revoked_at = datetime.now(UTC)
    assignment.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="role.revoked",
        target_type="role_assignment",
        target_id=assignment.id,
    )
    return Response(status_code=204)


@router.get("/tenants/{tenant_id}/security-policy")
def get_security_policy(
    tenant_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _tenant_actor(session, principal, tenant_id, "security_policy:read")
    policy = session.get(TenantSecurityPolicy, tenant_id)
    if policy is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, policy.version)
    return {
        "tenant_id": tenant_id,
        "mfa_required_for_all": policy.mfa_required_for_all,
        "session_max_minutes": policy.session_max_minutes,
        "version": policy.version,
    }


@router.patch("/tenants/{tenant_id}/security-policy")
@idempotent
def update_security_policy(
    tenant_id: str,
    body: SecurityPolicyUpdate,
    response: Response,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "security_policy:update")
    _require_mfa(request, principal)
    policy = session.get(TenantSecurityPolicy, tenant_id)
    if policy is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _require_version(if_match, policy.version)
    for name, value in body.model_dump(exclude_none=True).items():
        setattr(policy, name, value)
    policy.version += 1
    _etag(response, policy.version)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="security_policy.updated",
        target_type="tenant_security_policy",
        target_id=tenant_id,
    )
    return {
        "tenant_id": tenant_id,
        "mfa_required_for_all": policy.mfa_required_for_all,
        "session_max_minutes": policy.session_max_minutes,
        "version": policy.version,
    }


@router.post("/tenants/{tenant_id}/support-access-grants", status_code=201)
@idempotent
def request_support_access(
    tenant_id: str,
    body: SupportGrantCreate,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "support_access:approve")
    _require_mfa(request, principal)
    now = datetime.now(UTC)
    grant = SupportAccessGrant(
        tenant_id=tenant_id,
        support_user_id=body.support_user_id,
        reason=body.reason,
        ticket_reference=body.ticket_reference,
        scope=body.scope,
        starts_at=now,
        expires_at=now + timedelta(minutes=body.duration_minutes),
    )
    session.add(grant)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="support_access.requested",
        target_type="support_access_grant",
        target_id=grant.id,
    )
    return {"id": grant.id, "status": "pending", "expires_at": grant.expires_at}


@router.post("/tenants/{tenant_id}/support-access-grants/{grant_id}/approve")
@idempotent
def approve_support_access(
    tenant_id: str,
    grant_id: str,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "support_access:approve")
    _require_mfa(request, principal)
    grant = session.scalar(
        select(SupportAccessGrant).where(
            SupportAccessGrant.tenant_id == tenant_id,
            SupportAccessGrant.id == grant_id,
        )
    )
    if grant is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    if grant.approved_at or grant.revoked_at or _as_utc(grant.expires_at) <= datetime.now(UTC):
        raise ApiError(409, "state_conflict", "The support grant cannot be approved")
    if grant.support_user_id == actor.id:
        raise ApiError(403, "permission_denied", "Self-approval is prohibited")
    grant.approved_by_user_id = actor.id
    grant.approved_at = datetime.now(UTC)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="support_access.approved",
        target_type="support_access_grant",
        target_id=grant.id,
    )
    return {"id": grant.id, "status": "approved", "expires_at": grant.expires_at}


@router.post("/tenants/{tenant_id}/support-access-grants/{grant_id}/revoke")
@idempotent
def revoke_support_access(
    tenant_id: str,
    grant_id: str,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, str]:
    actor, _ = _tenant_actor(session, principal, tenant_id, "support_access:approve")
    _require_mfa(request, principal)
    grant = session.scalar(
        select(SupportAccessGrant).where(
            SupportAccessGrant.tenant_id == tenant_id,
            SupportAccessGrant.id == grant_id,
            SupportAccessGrant.revoked_at.is_(None),
        )
    )
    if grant is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    grant.revoked_at = datetime.now(UTC)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="support_access.revoked",
        target_type="support_access_grant",
        target_id=grant.id,
    )
    return {"id": grant.id, "status": "revoked"}
