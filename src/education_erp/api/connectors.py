"""Authorized generated-mock connector APIs."""

from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from education_erp.api.dependencies import (
    current_user,
    database_session,
    tenant_context,
    token_principal,
)
from education_erp.api.phase2 import audit
from education_erp.api.phase2_controls import bound_page, decode_bound_cursor, idempotent
from education_erp.canonical.service import require_mfa, require_scope
from education_erp.connectors.generated_mock import adapter_for
from education_erp.connectors.service import (
    execute_job,
    mapping_checksum,
    replay_dead_letter_record,
    safe_mapping_document,
)
from education_erp.connectors.synthetic_reference import (
    PACKAGE_ID,
    PACKAGE_VERSION,
    schema_checksum,
    verify_package,
)
from education_erp.errors import ApiError
from education_erp.identity.principal import TokenPrincipal
from education_erp.persistence.connector_models import (
    Connector,
    ConnectorBatch,
    DeadLetter,
    MappingSet,
    MappingVersion,
    ReconciliationRun,
    SourceSchema,
    StagingRecord,
    SyncJob,
    TransportConfig,
    ValidationError,
)
from education_erp.persistence.phase3_models import SourceAuthorityRule, SourceSystem

router = APIRouter(tags=["generated-mock-connectors"])
SessionDependency = Annotated[Session, Depends(database_session)]
PrincipalDependency = Annotated[TokenPrincipal, Depends(token_principal)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConnectorCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["generated_mock_v1", "synthetic_reference_erp_v1"]
    package_version: Literal["1.0.0"] | None = None
    scenario: Literal[
        "valid",
        "mixed",
        "duplicates",
        "late",
        "schema-drift-extra-field",
        "prohibited-child-attribute",
        "duplicate-version",
        "ambiguous-identity",
        "late-correction",
        "transport-timeout",
        "transport-throttled",
        "credential-rejected",
        "oversized-record",
    ] = "valid"


class ConnectorUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    status: Literal["active", "disabled"] | None = None
    scenario: str | None = Field(default=None, min_length=1, max_length=40)


class SyncCreate(StrictModel):
    connector_id: str
    scenario: str | None = Field(default=None, min_length=1, max_length=40)
    test_clock: datetime | None = None


class ReplayInput(StrictModel):
    reason: str = Field(min_length=8, max_length=500)


def _context(session: Session, principal: TokenPrincipal, tenant_id: str, permission: str) -> Any:
    context = tenant_context(session, principal, tenant_id)
    require_scope(context, permission)
    return context


def _connector(session: Session, tenant_id: str, connector_id: str) -> Connector:
    item = session.scalar(
        select(Connector).where(Connector.tenant_id == tenant_id, Connector.id == connector_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return item


def _serialize(item: Any) -> dict[str, object]:
    excluded = {"config", "normalized_document", "source_key_fingerprint", "deduplication_key"}
    result = {
        key: value
        for key, value in vars(item).items()
        if not key.startswith("_") and key not in excluded
    }
    if isinstance(item, Connector):
        result["scenario"] = item.config.get("scenario")
    return result


def _list(
    session: Session,
    model: Any,
    tenant_id: str,
    collection: str,
    cursor: str | None,
    limit: int,
    *criteria: Any,
    filters: str = "",
) -> dict[str, object]:
    boundary = decode_bound_cursor(
        cursor, tenant_id=tenant_id, collection=collection, filters=filters
    )
    statement = select(model).where(model.tenant_id == tenant_id, *criteria)
    if boundary:
        statement = statement.where(model.id > boundary)
    rows = list(session.scalars(statement.order_by(model.id).limit(limit + 1)))
    result = bound_page(rows, limit, tenant_id=tenant_id, collection=collection, filters=filters)
    result["items"] = [_serialize(row) for row in cast(list[Any], result["items"])]
    return result


@router.post("/tenants/{tenant_id}/connectors", status_code=201)
@idempotent
def create_connector(
    tenant_id: str,
    body: ConnectorCreate,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:manage")
    actor = current_user(session, principal)
    if (
        body.kind == "synthetic_reference_erp_v1"
        and not request.app.state.settings.demo_connector_enabled
    ):
        raise ApiError(403, "connector_kind_not_enabled", "The connector kind is not enabled")
    if body.kind == "synthetic_reference_erp_v1" and body.package_version != PACKAGE_VERSION:
        raise ApiError(422, "invalid_connector_config", "The approved package version is required")
    if body.kind == "generated_mock_v1" and body.package_version is not None:
        raise ApiError(422, "invalid_connector_config", "Package version is not accepted")
    adapter_for(body.kind, body.scenario)
    connector = Connector(
        tenant_id=tenant_id,
        name=body.name,
        kind=body.kind,
        config={
            "scenario": body.scenario,
            **(
                {"package_id": PACKAGE_ID, "package_version": PACKAGE_VERSION}
                if body.kind == "synthetic_reference_erp_v1"
                else {}
            ),
        },
    )
    session.add(connector)
    session.flush()
    document = safe_mapping_document()
    source_schema = None
    if body.kind == "synthetic_reference_erp_v1":
        source_schema = SourceSchema(
            tenant_id=tenant_id,
            connector_id=connector.id,
            package_id=PACKAGE_ID,
            package_version=PACKAGE_VERSION,
            schema_version="1",
            schema_checksum=schema_checksum(),
        )
        transport = TransportConfig(
            tenant_id=tenant_id,
            connector_id=connector.id,
            kind="in_process_csv_test_double",
            network_egress=False,
            credential_reference=None,
        )
        session.add_all([source_schema, transport])
        session.flush()
    mapping_set = MappingSet(
        tenant_id=tenant_id,
        connector_id=connector.id,
        name=(
            "synthetic-reference-canonical-v1" if source_schema else "generated-mock-canonical-v1"
        ),
    )
    session.add(mapping_set)
    session.flush()
    mapping = MappingVersion(
        tenant_id=tenant_id,
        connector_id=connector.id,
        mapping_set_id=mapping_set.id,
        source_schema_id=source_schema.id if source_schema else None,
        version=1,
        document=document,
        checksum=mapping_checksum(document),
    )
    source = SourceSystem(
        tenant_id=tenant_id,
        code=(f"synthetic-{connector.id}" if source_schema else f"mock-{connector.id}"),
        display_name=(
            f"Synthetic Reference ERP: {body.name}"
            if source_schema
            else f"Generated mock: {body.name}"
        ),
    )
    session.add_all([mapping, source])
    session.flush()
    session.add_all(
        [
            SourceAuthorityRule(
                tenant_id=tenant_id,
                source_system_id=source.id,
                entity_type=entity_type,
                authority="primary",
                effective_from=date(2030, 1, 1) if source_schema else date(2000, 1, 1),
            )
            for entity_type in (
                "academic-period",
                "programme",
                "programme-version",
                "course",
                "course-version",
                "offering",
                "learner",
                "programme-enrolment",
                "offering-enrolment",
            )
        ]
    )
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="connector.created",
        target_type="connector",
        target_id=connector.id,
        changes={"kind": connector.kind},
    )
    return _serialize(connector)


@router.get("/tenants/{tenant_id}/connectors")
def list_connectors(
    tenant_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:read")
    return _list(session, Connector, tenant_id, "connectors", cursor, limit)


@router.get("/tenants/{tenant_id}/connectors/{connector_id}")
def get_connector(
    tenant_id: str,
    connector_id: str,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:read")
    item = _connector(session, tenant_id, connector_id)
    response.headers["ETag"] = f'W/"{item.version}"'
    return _serialize(item)


@router.patch("/tenants/{tenant_id}/connectors/{connector_id}")
@idempotent
def update_connector(
    tenant_id: str,
    connector_id: str,
    body: ConnectorUpdate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: PrincipalDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:manage")
    item = _connector(session, tenant_id, connector_id)
    if if_match is None:
        raise ApiError(428, "precondition_required", "If-Match is required")
    if if_match != f'W/"{item.version}"':
        raise ApiError(412, "precondition_failed", "The resource version is stale")
    if body.name is not None:
        item.name = body.name
    if body.status is not None:
        item.status = body.status
    if body.scenario is not None:
        adapter_for(item.kind, body.scenario)
        item.config = {**item.config, "scenario": body.scenario}
    item.version += 1
    actor = current_user(session, principal)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="connector.updated",
        target_type="connector",
        target_id=item.id,
    )
    response.headers["ETag"] = f'W/"{item.version}"'
    return _serialize(item)


@router.post("/tenants/{tenant_id}/connectors/{connector_id}/test")
@idempotent
def test_connector(
    tenant_id: str,
    connector_id: str,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:run")
    item = _connector(session, tenant_id, connector_id)
    manifest = verify_package() if item.kind == "synthetic_reference_erp_v1" else None
    batch = adapter_for(item.kind, str(item.config["scenario"])).read_batch("0", 1)
    return {
        "connector_id": item.id,
        "status": "ok",
        "contract_version": "1",
        "sample_count": len(batch.records),
        "package_version": manifest["package_version"] if manifest else None,
        "network_egress": False,
        "credential_reference": None,
    }


@router.post("/tenants/{tenant_id}/sync-jobs", status_code=201)
@idempotent
def create_sync_job(
    tenant_id: str,
    body: SyncCreate,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:run")
    connector = _connector(session, tenant_id, body.connector_id)
    if connector.status != "active":
        raise ApiError(409, "connector_inactive", "The connector is not active")
    mapping = session.scalar(
        select(MappingVersion)
        .where(
            MappingVersion.tenant_id == tenant_id,
            MappingVersion.connector_id == connector.id,
            MappingVersion.active.is_(True),
        )
        .order_by(MappingVersion.version.desc())
    )
    if mapping is None:
        raise ApiError(409, "mapping_invalid", "No active mapping exists")
    actor = current_user(session, principal)
    scenario = body.scenario or str(connector.config["scenario"])
    adapter_for(connector.kind, scenario)
    job = SyncJob(
        tenant_id=tenant_id,
        connector_id=connector.id,
        mapping_version_id=mapping.id,
        scenario=scenario,
        requested_by_user_id=actor.id,
        package_version_snapshot=PACKAGE_VERSION
        if connector.kind == "synthetic_reference_erp_v1"
        else None,
        schema_version_snapshot="1" if connector.kind == "synthetic_reference_erp_v1" else None,
        threshold_version_snapshot="1" if connector.kind == "synthetic_reference_erp_v1" else None,
        test_clock=body.test_clock,
    )
    session.add(job)
    session.flush()
    execute_job(session, tenant_id=tenant_id, job_id=job.id)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="connector.sync_executed",
        target_type="sync_job",
        target_id=job.id,
    )
    return _serialize(job)


@router.get("/tenants/{tenant_id}/sync-jobs/{job_id}")
def get_job(
    tenant_id: str, job_id: str, session: SessionDependency, principal: PrincipalDependency
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:read")
    job = session.scalar(
        select(SyncJob).where(SyncJob.tenant_id == tenant_id, SyncJob.id == job_id)
    )
    if job is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return _serialize(job)


@router.get("/tenants/{tenant_id}/connectors/{connector_id}/runs")
def list_runs(
    tenant_id: str,
    connector_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:read")
    _connector(session, tenant_id, connector_id)
    return _list(
        session,
        SyncJob,
        tenant_id,
        "connector-runs",
        cursor,
        limit,
        SyncJob.connector_id == connector_id,
        filters=f"connector_id={connector_id}",
    )


@router.get("/tenants/{tenant_id}/reconciliation-runs/{run_id}")
def get_reconciliation(
    tenant_id: str, run_id: str, session: SessionDependency, principal: PrincipalDependency
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:reconcile")
    item = session.scalar(
        select(ReconciliationRun).where(
            ReconciliationRun.tenant_id == tenant_id, ReconciliationRun.id == run_id
        )
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    return _serialize(item)


@router.get("/tenants/{tenant_id}/sync-jobs/{job_id}/quarantine")
def list_quarantine(
    tenant_id: str,
    job_id: str,
    session: SessionDependency,
    principal: PrincipalDependency,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    _context(session, principal, tenant_id, "connector:reconcile")
    job = session.scalar(
        select(SyncJob.id).where(SyncJob.tenant_id == tenant_id, SyncJob.id == job_id)
    )
    if job is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    # Return only safe error metadata; no normalized or rejected values.
    boundary = decode_bound_cursor(
        cursor,
        tenant_id=tenant_id,
        collection="connector-quarantine",
        filters=f"job_id={job_id}",
    )
    statement = (
        select(ValidationError)
        .join(StagingRecord, StagingRecord.id == ValidationError.staging_record_id)
        .join(ConnectorBatch, ConnectorBatch.id == StagingRecord.batch_id)
        .where(
            ValidationError.tenant_id == tenant_id,
            StagingRecord.outcome == "quarantined",
            ConnectorBatch.job_id == job_id,
        )
    )
    if boundary:
        statement = statement.where(ValidationError.id > boundary)
    rows = list(session.scalars(statement.order_by(ValidationError.id).limit(limit + 1)))
    result = bound_page(
        rows,
        limit,
        tenant_id=tenant_id,
        collection="connector-quarantine",
        filters=f"job_id={job_id}",
    )
    result["items"] = [
        {
            "id": row.id,
            "code": row.code,
            "field_path": row.field_path,
            "rule_version": row.rule_version,
        }
        for row in cast(list[ValidationError], result["items"])
    ]
    return result


@router.post("/tenants/{tenant_id}/dead-letters/{dead_letter_id}/replay")
@idempotent
def replay_dead_letter(
    tenant_id: str,
    dead_letter_id: str,
    body: ReplayInput,
    request: Request,
    session: SessionDependency,
    principal: PrincipalDependency,
) -> dict[str, object]:
    context = _context(session, principal, tenant_id, "connector:replay")
    require_mfa(context)
    if datetime.now(UTC) - principal.issued_at > timedelta(minutes=15):
        raise ApiError(403, "recent_authentication_required", "Recent authentication is required")
    item = session.scalar(
        select(DeadLetter).where(DeadLetter.tenant_id == tenant_id, DeadLetter.id == dead_letter_id)
    )
    if item is None:
        raise ApiError(404, "resource_not_found", "The requested resource was not found")
    if item.replay_state != "available":
        raise ApiError(409, "replay_unavailable", "Replay is unavailable")
    item = replay_dead_letter_record(session, tenant_id=tenant_id, dead_letter_id=item.id)
    actor = current_user(session, principal)
    audit(
        session,
        request,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="connector.replay_requested",
        target_type="dead_letter",
        target_id=item.id,
        reason=body.reason,
    )
    return {"id": item.id, "replay_state": item.replay_state, "attempts": item.attempts}
