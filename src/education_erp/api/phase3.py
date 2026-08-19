"""Approved Phase 3 canonical education APIs."""

from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from education_erp.access.policy import TenantContext
from education_erp.api.dependencies import database_session, tenant_context, token_principal
from education_erp.api.phase2 import audit
from education_erp.api.phase2_controls import bound_page, decode_bound_cursor, idempotent
from education_erp.canonical.service import (
    fingerprint,
    mask_reference,
    normalized_code,
    require_mfa,
    require_scope,
    require_unrestricted,
    transition_enrolment,
    validate_interval,
)
from education_erp.errors import ApiError
from education_erp.identity.principal import TokenPrincipal
from education_erp.persistence.phase3_models import (
    AcademicPeriod,
    AcademicPeriodLineageLink,
    Course,
    CourseLineageLink,
    CourseVersion,
    CourseVersionLineageLink,
    EnrolmentStatusHistory,
    Learner,
    LearnerLineageLink,
    Offering,
    OfferingEnrolment,
    OfferingEnrolmentLineageLink,
    OfferingLineageLink,
    Programme,
    ProgrammeEnrolment,
    ProgrammeEnrolmentLineageLink,
    ProgrammeLineageLink,
    ProgrammeVersion,
    ProgrammeVersionLineageLink,
    ReconciliationIssue,
    SourceAuthorityRule,
    SourceObservation,
    SourceSystem,
    SubjectExportManifest,
    SubjectRightsRequest,
)

router = APIRouter(tags=["canonical-education"])
SessionDependency = Annotated[Session, Depends(database_session)]
PrincipalDependency = Annotated[TokenPrincipal, Depends(token_principal)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PeriodInput(StrictModel):
    code: str
    name: str = Field(min_length=1, max_length=200)
    period_type: Literal["year", "term", "semester", "quarter"]
    starts_on: date
    ends_on: date
    parent_period_id: str | None = None


class RootInput(StrictModel):
    code: str


class VersionInput(StrictModel):
    version_code: str
    name: str | None = Field(default=None, min_length=1, max_length=200)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    credit_value: float | None = Field(default=None, ge=0, le=999.99)
    effective_from: date
    effective_to: date | None = None


class OfferingInput(StrictModel):
    code: str
    academic_period_id: str
    course_version_id: str
    campus_id: str | None = None
    department_id: str | None = None


class LearnerInput(StrictModel):
    institution_reference: str = Field(min_length=1, max_length=200)
    platform_user_id: str | None = None


class EnrolmentInput(StrictModel):
    learner_id: str
    target_id: str
    effective_from: date
    effective_to: date | None = None


class ReasonInput(StrictModel):
    reason: str = Field(min_length=8, max_length=500)


class ReconcileInput(ReasonInput):
    resolution_code: Literal["accept_primary", "accept_manual", "equivalent", "dismissed"]


class SubjectRequestInput(StrictModel):
    learner_id: str
    request_type: Literal["access", "correction", "restriction", "deletion"]
    due_at: datetime
    reason_code: str = Field(min_length=2, max_length=40)


def _context(
    session: Session, principal: TokenPrincipal, tenant_id: str, permission: str
) -> TenantContext:
    context = tenant_context(session, principal, tenant_id)
    require_scope(context, permission)
    return context


def _etag(response: Response, version: int) -> None:
    response.headers["ETag"] = f'W/"{version}"'


def _match(if_match: str | None, version: int) -> None:
    if if_match is None:
        raise ApiError(428, "precondition_required", "If-Match is required")
    if if_match != f'W/"{version}"':
        raise ApiError(412, "precondition_failed", "The resource version is stale")


def _serialize(item: Any) -> dict[str, object]:
    return {
        key: value
        for key, value in vars(item).items()
        if not key.startswith("_")
        and key
        not in {
            "institution_reference",
            "institution_reference_fingerprint",
            "source_record_key",
            "source_record_fingerprint",
            "semantic_hash",
        }
    }


def _list(
    session: Session,
    model: Any,
    tenant_id: str,
    cursor: str | None,
    limit: int,
) -> dict[str, object]:
    collection = str(model.__tablename__)
    boundary = decode_bound_cursor(cursor, tenant_id=tenant_id, collection=collection)
    statement = select(model).where(model.tenant_id == tenant_id)
    if boundary:
        statement = statement.where(model.id > boundary)
    items = list(session.scalars(statement.order_by(model.id).limit(limit + 1)))
    result = bound_page(items, limit, tenant_id=tenant_id, collection=collection)
    result["items"] = [_serialize(item) for item in cast(list[Any], result["items"])]
    return result


@router.get("/tenants/{tenant_id}/academic-periods")
def list_periods(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "academic_structure:read")
    return _list(session, AcademicPeriod, tenant_id, cursor, limit)


@router.post("/tenants/{tenant_id}/academic-periods", status_code=201)
@idempotent
def create_period(
    tenant_id: str,
    body: PeriodInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "academic_structure:manage")
    if body.ends_on < body.starts_on:
        raise ApiError(409, "temporal_conflict", "The period interval is invalid")
    item = AcademicPeriod(
        tenant_id=tenant_id,
        code=normalized_code(body.code),
        name=body.name,
        period_type=body.period_type,
        starts_on=body.starts_on,
        ends_on=body.ends_on,
        parent_period_id=body.parent_period_id,
    )
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="academic_period.created",
        target_type="academic_period",
        target_id=item.id,
    )
    return _serialize(item)


@router.get("/tenants/{tenant_id}/academic-periods/{period_id}")
def get_period(
    tenant_id: str,
    period_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "academic_structure:read")
    item = session.scalar(
        select(AcademicPeriod).where(
            AcademicPeriod.id == period_id, AcademicPeriod.tenant_id == tenant_id
        )
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, item.version)
    return _serialize(item)


@router.patch("/tenants/{tenant_id}/academic-periods/{period_id}")
@idempotent
def update_period(
    tenant_id: str,
    period_id: str,
    body: PeriodInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "academic_structure:manage")
    item = session.scalar(
        select(AcademicPeriod).where(
            AcademicPeriod.id == period_id, AcademicPeriod.tenant_id == tenant_id
        )
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.code, item.name, item.period_type = normalized_code(body.code), body.name, body.period_type
    item.starts_on, item.ends_on, item.parent_period_id = (
        body.starts_on,
        body.ends_on,
        body.parent_period_id,
    )
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="academic_period.updated",
        target_type="academic_period",
        target_id=item.id,
    )
    return _serialize(item)


def _root_list(
    session: Session, model: Any, tenant_id: str, cursor: str | None, limit: int
) -> dict[str, object]:
    return _list(session, model, tenant_id, cursor, limit)


@router.get("/tenants/{tenant_id}/programmes")
def list_programmes(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "academic_structure:read")
    return _root_list(session, Programme, tenant_id, cursor, limit)


@router.post("/tenants/{tenant_id}/programmes", status_code=201)
@idempotent
def create_programme(
    tenant_id: str,
    body: RootInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "academic_structure:manage")
    item = Programme(tenant_id=tenant_id, code=normalized_code(body.code))
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="programme.created",
        target_type="programme",
        target_id=item.id,
    )
    return _serialize(item)


@router.get("/tenants/{tenant_id}/programmes/{programme_id}")
def get_programme(
    tenant_id: str,
    programme_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "academic_structure:read")
    item = session.scalar(
        select(Programme).where(Programme.id == programme_id, Programme.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, item.version)
    return _serialize(item)


@router.patch("/tenants/{tenant_id}/programmes/{programme_id}")
@idempotent
def update_programme(
    tenant_id: str,
    programme_id: str,
    body: RootInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "academic_structure:manage")
    item = session.scalar(
        select(Programme).where(Programme.id == programme_id, Programme.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.code = normalized_code(body.code)
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="programme.updated",
        target_type="programme",
        target_id=item.id,
    )
    return _serialize(item)


@router.post("/tenants/{tenant_id}/programmes/{programme_id}/versions", status_code=201)
@idempotent
def create_programme_version(
    tenant_id: str,
    programme_id: str,
    body: VersionInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "academic_structure:manage")
    validate_interval(body.effective_from, body.effective_to)
    if (
        session.scalar(
            select(Programme.id).where(
                Programme.id == programme_id, Programme.tenant_id == tenant_id
            )
        )
        is None
        or body.name is None
    ):
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    item = ProgrammeVersion(
        tenant_id=tenant_id,
        programme_id=programme_id,
        version_code=normalized_code(body.version_code),
        name=body.name,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
    )
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="programme_version.created",
        target_type="programme_version",
        target_id=item.id,
    )
    return _serialize(item)


@router.get("/tenants/{tenant_id}/courses")
def list_courses(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "academic_structure:read")
    return _root_list(session, Course, tenant_id, cursor, limit)


@router.post("/tenants/{tenant_id}/courses", status_code=201)
@idempotent
def create_course(
    tenant_id: str,
    body: RootInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "academic_structure:manage")
    item = Course(tenant_id=tenant_id, code=normalized_code(body.code))
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="course.created",
        target_type="course",
        target_id=item.id,
    )
    return _serialize(item)


@router.get("/tenants/{tenant_id}/courses/{course_id}")
def get_course(
    tenant_id: str,
    course_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "academic_structure:read")
    item = session.scalar(
        select(Course).where(Course.id == course_id, Course.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, item.version)
    return _serialize(item)


@router.patch("/tenants/{tenant_id}/courses/{course_id}")
@idempotent
def update_course(
    tenant_id: str,
    course_id: str,
    body: RootInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "academic_structure:manage")
    item = session.scalar(
        select(Course).where(Course.id == course_id, Course.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.code = normalized_code(body.code)
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="course.updated",
        target_type="course",
        target_id=item.id,
    )
    return _serialize(item)


@router.post("/tenants/{tenant_id}/courses/{course_id}/versions", status_code=201)
@idempotent
def create_course_version(
    tenant_id: str,
    course_id: str,
    body: VersionInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "academic_structure:manage")
    validate_interval(body.effective_from, body.effective_to)
    if (
        session.scalar(
            select(Course.id).where(Course.id == course_id, Course.tenant_id == tenant_id)
        )
        is None
        or body.title is None
    ):
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    item = CourseVersion(
        tenant_id=tenant_id,
        course_id=course_id,
        version_code=normalized_code(body.version_code),
        title=body.title,
        credit_value=body.credit_value,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
    )
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="course_version.created",
        target_type="course_version",
        target_id=item.id,
    )
    return _serialize(item)


@router.get("/tenants/{tenant_id}/offerings")
def list_offerings(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "academic_structure:read")
    return _list(session, Offering, tenant_id, cursor, limit)


@router.post("/tenants/{tenant_id}/offerings", status_code=201)
@idempotent
def create_offering(
    tenant_id: str,
    body: OfferingInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = tenant_context(session, principal, tenant_id)
    require_scope(context, "academic_structure:manage", body.campus_id, body.department_id)
    item = Offering(
        tenant_id=tenant_id,
        code=normalized_code(body.code),
        academic_period_id=body.academic_period_id,
        course_version_id=body.course_version_id,
        campus_id=body.campus_id,
        department_id=body.department_id,
    )
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="offering.created",
        target_type="offering",
        target_id=item.id,
    )
    return _serialize(item)


@router.get("/tenants/{tenant_id}/offerings/{offering_id}")
def get_offering(
    tenant_id: str,
    offering_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "academic_structure:read")
    item = session.scalar(
        select(Offering).where(Offering.id == offering_id, Offering.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, item.version)
    return _serialize(item)


@router.patch("/tenants/{tenant_id}/offerings/{offering_id}")
@idempotent
def update_offering(
    tenant_id: str,
    offering_id: str,
    body: OfferingInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = tenant_context(session, principal, tenant_id)
    require_scope(context, "academic_structure:manage", body.campus_id, body.department_id)
    item = session.scalar(
        select(Offering).where(Offering.id == offering_id, Offering.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.code = normalized_code(body.code)
    item.academic_period_id, item.course_version_id = (
        body.academic_period_id,
        body.course_version_id,
    )
    item.campus_id, item.department_id = body.campus_id, body.department_id
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="offering.updated",
        target_type="offering",
        target_id=item.id,
    )
    return _serialize(item)


def _learner_dict(item: Learner) -> dict[str, object]:
    result = _serialize(item)
    result["institution_reference_masked"] = mask_reference(item.institution_reference)
    return result


@router.get("/tenants/{tenant_id}/learners")
def list_learners(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "learner:read")
    boundary = decode_bound_cursor(cursor, tenant_id=tenant_id, collection="learners")
    statement = select(Learner).where(Learner.tenant_id == tenant_id)
    if boundary:
        statement = statement.where(Learner.id > boundary)
    items = list(session.scalars(statement.order_by(Learner.id).limit(limit + 1)))
    result = bound_page(items, limit, tenant_id=tenant_id, collection="learners")
    result["items"] = [_learner_dict(item) for item in cast(list[Learner], result["items"])]
    return result


@router.post("/tenants/{tenant_id}/learners", status_code=201)
@idempotent
def create_learner(
    tenant_id: str,
    body: LearnerInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "learner:manage")
    item = Learner(
        tenant_id=tenant_id,
        institution_reference=body.institution_reference,
        institution_reference_fingerprint=fingerprint(tenant_id, body.institution_reference),
        platform_user_id=body.platform_user_id,
    )
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="learner.created",
        target_type="learner",
        target_id=item.id,
        changes={"fields": ["institution_reference"]},
    )
    return _learner_dict(item)


@router.get("/tenants/{tenant_id}/learners/{learner_id}")
def get_learner(
    tenant_id: str,
    learner_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "learner:read")
    item = session.scalar(
        select(Learner).where(Learner.id == learner_id, Learner.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, item.version)
    return _learner_dict(item)


@router.patch("/tenants/{tenant_id}/learners/{learner_id}")
@idempotent
def update_learner(
    tenant_id: str,
    learner_id: str,
    body: LearnerInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "learner:manage")
    item = session.scalar(
        select(Learner).where(Learner.id == learner_id, Learner.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    require_unrestricted(item.processing_restricted)
    _match(if_match, item.version)
    item.institution_reference = body.institution_reference
    item.institution_reference_fingerprint = fingerprint(tenant_id, body.institution_reference)
    item.platform_user_id = body.platform_user_id
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="learner.updated",
        target_type="learner",
        target_id=item.id,
        changes={"fields": ["institution_reference"]},
    )
    return _learner_dict(item)


@router.post("/tenants/{tenant_id}/learners/{learner_id}/restrict-processing")
@idempotent
def restrict_learner(
    tenant_id: str,
    learner_id: str,
    body: ReasonInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "subject_rights:manage")
    require_mfa(context)
    item = session.scalar(
        select(Learner).where(Learner.id == learner_id, Learner.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.processing_restricted = True
    item.restriction_reason_code = "subject_request"
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="learner.processing_restricted",
        target_type="learner",
        target_id=item.id,
        reason=body.reason,
    )
    return _learner_dict(item)


@router.post("/tenants/{tenant_id}/learners/{learner_id}/resume-processing")
@idempotent
def resume_learner(
    tenant_id: str,
    learner_id: str,
    body: ReasonInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "subject_rights:manage")
    require_mfa(context)
    item = session.scalar(
        select(Learner).where(Learner.id == learner_id, Learner.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.processing_restricted = False
    item.restriction_reason_code = None
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="learner.processing_resumed",
        target_type="learner",
        target_id=item.id,
        reason=body.reason,
    )
    return _learner_dict(item)


@router.post("/tenants/{tenant_id}/learners/{learner_id}/reveal-reference")
def reveal_reference(
    tenant_id: str,
    learner_id: str,
    body: ReasonInput,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, str]:
    context = _context(session, principal, tenant_id, "learner_identifier:read")
    require_mfa(context)
    item = session.scalar(
        select(Learner).where(Learner.id == learner_id, Learner.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="learner.reference_revealed",
        target_type="learner",
        target_id=item.id,
        reason=body.reason,
    )
    response.headers["Cache-Control"] = "no-store"
    return {"institution_reference": item.institution_reference}


def _enrolment_model(kind: str) -> Any:
    return ProgrammeEnrolment if kind == "programme" else OfferingEnrolment


@router.get("/tenants/{tenant_id}/{kind}-enrolments")
def list_enrolments(
    tenant_id: str,
    kind: Literal["programme", "offering"],
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "enrolment:read")
    return _list(session, _enrolment_model(kind), tenant_id, cursor, limit)


@router.post("/tenants/{tenant_id}/{kind}-enrolments", status_code=201)
@idempotent
def create_enrolment(
    tenant_id: str,
    kind: Literal["programme", "offering"],
    body: EnrolmentInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "enrolment:manage")
    validate_interval(body.effective_from, body.effective_to)
    learner = session.scalar(
        select(Learner).where(Learner.id == body.learner_id, Learner.tenant_id == tenant_id)
    )
    if learner is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    require_unrestricted(learner.processing_restricted)
    model = _enrolment_model(kind)
    kwargs = (
        {"programme_version_id": body.target_id}
        if kind == "programme"
        else {"offering_id": body.target_id}
    )
    item = model(
        tenant_id=tenant_id,
        learner_id=body.learner_id,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        **kwargs,
    )
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action=f"{kind}_enrolment.created",
        target_type=f"{kind}_enrolment",
        target_id=item.id,
    )
    return _serialize(item)


@router.get("/tenants/{tenant_id}/{kind}-enrolments/{enrolment_id}")
def get_enrolment(
    tenant_id: str,
    kind: Literal["programme", "offering"],
    enrolment_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "enrolment:read")
    model = _enrolment_model(kind)
    item = session.scalar(
        select(model).where(model.id == enrolment_id, model.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, item.version)
    return _serialize(item)


@router.post("/tenants/{tenant_id}/{kind}-enrolments/{enrolment_id}/{action}")
@idempotent
def transition_enrolment_route(
    tenant_id: str,
    kind: Literal["programme", "offering"],
    enrolment_id: str,
    action: str,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "enrolment:manage")
    model = _enrolment_model(kind)
    item = session.scalar(
        select(model).where(model.id == enrolment_id, model.tenant_id == tenant_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    learner = session.scalar(
        select(Learner).where(Learner.id == item.learner_id, Learner.tenant_id == tenant_id)
    )
    if learner is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    require_unrestricted(learner.processing_restricted)
    previous = item.status
    item.status = transition_enrolment(item.status, action)
    item.version += 1
    session.add(
        EnrolmentStatusHistory(
            tenant_id=tenant_id,
            enrolment_type=kind,
            enrolment_id=item.id,
            from_status=previous,
            to_status=item.status,
            reason_code=action,
            changed_by_user_id=context.user.id,
        )
    )
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action=f"{kind}_enrolment.{action}",
        target_type=f"{kind}_enrolment",
        target_id=item.id,
    )
    return _serialize(item)


LINEAGE_MODELS: dict[str, tuple[type[Any], str, type[Any]]] = {
    "academic-period": (AcademicPeriodLineageLink, "academic_period_id", AcademicPeriod),
    "programme": (ProgrammeLineageLink, "programme_id", Programme),
    "programme-version": (
        ProgrammeVersionLineageLink,
        "programme_version_id",
        ProgrammeVersion,
    ),
    "course": (CourseLineageLink, "course_id", Course),
    "course-version": (CourseVersionLineageLink, "course_version_id", CourseVersion),
    "offering": (OfferingLineageLink, "offering_id", Offering),
    "learner": (LearnerLineageLink, "learner_id", Learner),
    "programme-enrolment": (
        ProgrammeEnrolmentLineageLink,
        "programme_enrolment_id",
        ProgrammeEnrolment,
    ),
    "offering-enrolment": (
        OfferingEnrolmentLineageLink,
        "offering_enrolment_id",
        OfferingEnrolment,
    ),
}


@router.get("/tenants/{tenant_id}/canonical-records/{entity_type}/{record_id}/lineage")
def canonical_lineage(
    tenant_id: str,
    entity_type: str,
    record_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "lineage:read")
    require_mfa(context)
    configured = LINEAGE_MODELS.get(entity_type)
    if configured is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    link_model, target_attribute, target_model = configured
    target_exists = session.scalar(
        select(target_model.id).where(
            target_model.id == record_id,
            target_model.tenant_id == tenant_id,
        )
    )
    if target_exists is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    rows = session.execute(
        select(
            link_model,
            SourceObservation,
            SourceSystem.code,
            SourceAuthorityRule.authority,
        )
        .join(SourceObservation, SourceObservation.id == link_model.source_observation_id)
        .join(SourceSystem, SourceSystem.id == SourceObservation.source_system_id)
        .join(
            SourceAuthorityRule,
            (SourceAuthorityRule.tenant_id == SourceObservation.tenant_id)
            & (SourceAuthorityRule.source_system_id == SourceObservation.source_system_id)
            & (SourceAuthorityRule.entity_type == SourceObservation.entity_type)
            & (SourceAuthorityRule.effective_from <= func.date(SourceObservation.effective_at))
            & (
                SourceAuthorityRule.effective_to.is_(None)
                | (SourceAuthorityRule.effective_to > func.date(SourceObservation.effective_at))
            ),
        )
        .where(
            getattr(link_model, target_attribute) == record_id,
            link_model.tenant_id == tenant_id,
        )
    ).all()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="lineage.read",
        target_type=entity_type,
        target_id=record_id,
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "items": [
            {
                "source_code": source_code,
                "observation_id": observation.id,
                "source_record_version": observation.source_record_version,
                "mapping_version": observation.mapping_version,
                "authority": authority,
                "observed_at": observation.observed_at,
                "effective_at": observation.effective_at,
                "recorded_at": observation.created_at,
                "relationship": link.relationship,
            }
            for link, observation, source_code, authority in rows
        ],
        "next_cursor": None,
    }


@router.get("/tenants/{tenant_id}/reconciliation-issues")
def list_reconciliation(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "lineage:read")
    require_mfa(context)
    return _list(session, ReconciliationIssue, tenant_id, cursor, limit)


@router.get("/tenants/{tenant_id}/reconciliation-issues/{issue_id}")
def get_reconciliation(
    tenant_id: str,
    issue_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "lineage:read")
    require_mfa(context)
    item = session.scalar(
        select(ReconciliationIssue).where(
            ReconciliationIssue.id == issue_id, ReconciliationIssue.tenant_id == tenant_id
        )
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, item.version)
    response.headers["Cache-Control"] = "no-store"
    return _serialize(item)


@router.post("/tenants/{tenant_id}/reconciliation-issues/{issue_id}/resolve")
@idempotent
def resolve_reconciliation(
    tenant_id: str,
    issue_id: str,
    body: ReconcileInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "reconciliation:manage")
    require_mfa(context)
    item = session.scalar(
        select(ReconciliationIssue).where(
            ReconciliationIssue.id == issue_id,
            ReconciliationIssue.tenant_id == tenant_id,
        )
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.status = "resolved"
    item.resolution_code = body.resolution_code
    item.resolved_by_user_id = context.user.id
    item.resolved_at = datetime.now().astimezone()
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="reconciliation.resolved",
        target_type="reconciliation_issue",
        target_id=item.id,
        reason=body.reason,
    )
    return _serialize(item)


@router.post("/tenants/{tenant_id}/reconciliation-issues/{issue_id}/dismiss")
@idempotent
def dismiss_reconciliation(
    tenant_id: str,
    issue_id: str,
    body: ReasonInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "reconciliation:manage")
    require_mfa(context)
    item = session.scalar(
        select(ReconciliationIssue).where(
            ReconciliationIssue.id == issue_id, ReconciliationIssue.tenant_id == tenant_id
        )
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.status = "dismissed"
    item.resolution_code = "dismissed"
    item.resolved_by_user_id = context.user.id
    item.resolved_at = datetime.now(UTC)
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="reconciliation.dismissed",
        target_type="reconciliation_issue",
        target_id=item.id,
        reason=body.reason,
    )
    return _serialize(item)


@router.get("/tenants/{tenant_id}/subject-rights-requests")
def list_subject_requests(
    tenant_id: str,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    access_reason: Annotated[str, Header(alias="X-Access-Reason", min_length=8)],
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "subject_rights:read")
    require_mfa(context)
    result = _list(session, SubjectRightsRequest, tenant_id, cursor, limit)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="subject_rights.listed",
        target_type="subject_rights_request",
        target_id=None,
        reason=access_reason,
    )
    return result


@router.get("/tenants/{tenant_id}/subject-rights-requests/{subject_request_id}")
def get_subject_request(
    tenant_id: str,
    subject_request_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
    access_reason: Annotated[str, Header(alias="X-Access-Reason", min_length=8)],
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "subject_rights:read")
    require_mfa(context)
    item = session.scalar(
        select(SubjectRightsRequest).where(
            SubjectRightsRequest.id == subject_request_id,
            SubjectRightsRequest.tenant_id == tenant_id,
        )
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _etag(response, item.version)
    response.headers["Cache-Control"] = "no-store"
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="subject_rights.read",
        target_type="subject_rights_request",
        target_id=item.id,
        reason=access_reason,
    )
    return _serialize(item)


@router.post("/tenants/{tenant_id}/subject-rights-requests", status_code=201)
@idempotent
def create_subject_request(
    tenant_id: str,
    body: SubjectRequestInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "subject_rights:manage")
    require_mfa(context)
    if (
        session.scalar(
            select(Learner.id).where(Learner.id == body.learner_id, Learner.tenant_id == tenant_id)
        )
        is None
    ):
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    item = SubjectRightsRequest(
        tenant_id=tenant_id,
        learner_id=body.learner_id,
        request_type=body.request_type,
        due_at=body.due_at,
        reason_code=body.reason_code,
        created_by_user_id=context.user.id,
    )
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="subject_rights.created",
        target_type="subject_rights_request",
        target_id=item.id,
    )
    return _serialize(item)


@router.post("/tenants/{tenant_id}/subject-rights-requests/{subject_request_id}/complete")
@idempotent
def complete_subject_request(
    tenant_id: str,
    subject_request_id: str,
    body: ReasonInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "subject_rights:manage")
    require_mfa(context)
    item = session.scalar(
        select(SubjectRightsRequest).where(
            SubjectRightsRequest.id == subject_request_id,
            SubjectRightsRequest.tenant_id == tenant_id,
        )
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    _match(if_match, item.version)
    item.status = "completed"
    item.disposition_code = "fulfilled"
    item.version += 1
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="subject_rights.completed",
        target_type="subject_rights_request",
        target_id=item.id,
        reason=body.reason,
    )
    return _serialize(item)


@router.post(
    "/tenants/{tenant_id}/subject-rights-requests/{subject_request_id}/export-manifest",
    status_code=201,
)
@idempotent
def create_export_manifest(
    tenant_id: str,
    subject_request_id: str,
    body: ReasonInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "subject_export:create")
    require_mfa(context)
    subject_request = session.scalar(
        select(SubjectRightsRequest).where(
            SubjectRightsRequest.id == subject_request_id,
            SubjectRightsRequest.tenant_id == tenant_id,
        )
    )
    if subject_request is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    existing_manifest = session.scalar(
        select(SubjectExportManifest.id).where(
            SubjectExportManifest.tenant_id == tenant_id,
            SubjectExportManifest.request_id == subject_request_id,
        )
    )
    if existing_manifest is not None:
        raise ApiError(
            409,
            "state_conflict",
            "An export manifest already exists for this request",
        )
    item = SubjectExportManifest(
        tenant_id=tenant_id,
        learner_id=subject_request.learner_id,
        request_id=subject_request.id,
        created_by_user_id=context.user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    session.add(item)
    session.flush()
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=context.user.id,
        action="subject_export.manifest_created",
        target_type="subject_export_manifest",
        target_id=item.id,
        reason=body.reason,
    )
    return _serialize(item)
