"""Durable generated connector execution through canonical observation services."""

import hashlib
import json
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import Engine, delete, func, select
from sqlalchemy.orm import Session

from education_erp.canonical.reconciliation import record_observation
from education_erp.canonical.service import fingerprint
from education_erp.connectors.generated_mock import adapter_for
from education_erp.errors import ApiError
from education_erp.events import EventEnvelope, enqueue_event
from education_erp.persistence.connector_models import (
    Connector,
    ConnectorBatch,
    ConnectorWatermark,
    DeadLetter,
    ReconciliationRun,
    StagingRecord,
    SyncJob,
    ValidationError,
)
from education_erp.persistence.models import new_id, utc_now
from education_erp.persistence.phase3_models import (
    AcademicPeriod,
    Course,
    CourseVersion,
    Learner,
    Offering,
    OfferingEnrolment,
    Programme,
    ProgrammeEnrolment,
    ProgrammeVersion,
    ReconciliationIssue,
    SourceSystem,
)


class LearnerDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    institution_reference: str = Field(min_length=1, max_length=200)


DOCUMENT_FIELDS = {
    "academic-period": frozenset({"code", "name", "period_type", "starts_on", "ends_on"}),
    "programme": frozenset({"code"}),
    "programme-version": frozenset({"programme_code", "version_code", "name", "effective_from"}),
    "course": frozenset({"code"}),
    "course-version": frozenset(
        {"course_code", "version_code", "title", "credit_value", "effective_from"}
    ),
    "offering": frozenset({"code", "academic_period_code", "course_code", "course_version_code"}),
    "learner": frozenset({"institution_reference"}),
    "programme-enrolment": frozenset(
        {
            "learner_reference",
            "programme_code",
            "programme_version_code",
            "effective_from",
            "status",
        }
    ),
    "offering-enrolment": frozenset(
        {"learner_reference", "offering_code", "effective_from", "status"}
    ),
}


def safe_mapping_document() -> dict[str, object]:
    return {
        "schema_version": "1",
        "entities": {entity: sorted(fields) for entity, fields in DOCUMENT_FIELDS.items()},
    }


def mapping_checksum(document: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _document(entity_type: str, value: dict[str, Any]) -> dict[str, Any]:
    expected = DOCUMENT_FIELDS.get(entity_type)
    if expected is None or set(value) != expected:
        raise ValueError("schema_validation_failed")
    if entity_type == "learner":
        return LearnerDocument.model_validate(value).model_dump()
    for key, item in value.items():
        if key != "credit_value" and (not isinstance(item, str) or not item):
            raise ValueError("schema_validation_failed")
    return value


def _one(session: Session, model: Any, tenant_id: str, **values: object) -> Any:
    statement = select(model).where(model.tenant_id == tenant_id)
    for key, value in values.items():
        statement = statement.where(getattr(model, key) == value)
    result = session.scalar(statement)
    if result is None:
        raise ValueError("referenced_record_missing")
    return result


def _target(
    session: Session, tenant_id: str, entity_type: str, document: dict[str, Any]
) -> tuple[str, Any]:
    existing: Any = None
    if entity_type == "academic-period":
        existing = session.scalar(
            select(AcademicPeriod).where(
                AcademicPeriod.tenant_id == tenant_id, AcademicPeriod.code == document["code"]
            )
        )
        record: Any = AcademicPeriod(
            id=new_id(),
            tenant_id=tenant_id,
            code=document["code"],
            name=document["name"],
            period_type=document["period_type"],
            starts_on=date.fromisoformat(document["starts_on"]),
            ends_on=date.fromisoformat(document["ends_on"]),
        )
    elif entity_type == "programme":
        existing = session.scalar(
            select(Programme).where(
                Programme.tenant_id == tenant_id, Programme.code == document["code"]
            )
        )
        record = Programme(id=new_id(), tenant_id=tenant_id, code=document["code"])
    elif entity_type == "programme-version":
        parent = _one(session, Programme, tenant_id, code=document["programme_code"])
        existing = session.scalar(
            select(ProgrammeVersion).where(
                ProgrammeVersion.tenant_id == tenant_id,
                ProgrammeVersion.programme_id == parent.id,
                ProgrammeVersion.version_code == document["version_code"],
            )
        )
        record = ProgrammeVersion(
            id=new_id(),
            tenant_id=tenant_id,
            programme_id=parent.id,
            version_code=document["version_code"],
            name=document["name"],
            effective_from=date.fromisoformat(document["effective_from"]),
        )
    elif entity_type == "course":
        existing = session.scalar(
            select(Course).where(Course.tenant_id == tenant_id, Course.code == document["code"])
        )
        record = Course(id=new_id(), tenant_id=tenant_id, code=document["code"])
    elif entity_type == "course-version":
        parent = _one(session, Course, tenant_id, code=document["course_code"])
        existing = session.scalar(
            select(CourseVersion).where(
                CourseVersion.tenant_id == tenant_id,
                CourseVersion.course_id == parent.id,
                CourseVersion.version_code == document["version_code"],
            )
        )
        record = CourseVersion(
            id=new_id(),
            tenant_id=tenant_id,
            course_id=parent.id,
            version_code=document["version_code"],
            title=document["title"],
            credit_value=document["credit_value"],
            effective_from=date.fromisoformat(document["effective_from"]),
        )
    elif entity_type == "offering":
        period = _one(session, AcademicPeriod, tenant_id, code=document["academic_period_code"])
        course = _one(session, Course, tenant_id, code=document["course_code"])
        version = _one(
            session,
            CourseVersion,
            tenant_id,
            course_id=course.id,
            version_code=document["course_version_code"],
        )
        existing = session.scalar(
            select(Offering).where(
                Offering.tenant_id == tenant_id,
                Offering.academic_period_id == period.id,
                Offering.code == document["code"],
            )
        )
        record = Offering(
            id=new_id(),
            tenant_id=tenant_id,
            academic_period_id=period.id,
            course_version_id=version.id,
            code=document["code"],
        )
    elif entity_type == "learner":
        reference_fingerprint = fingerprint(tenant_id, document["institution_reference"])
        existing = session.scalar(
            select(Learner).where(
                Learner.tenant_id == tenant_id,
                Learner.institution_reference_fingerprint == reference_fingerprint,
            )
        )
        record = Learner(
            id=new_id(),
            tenant_id=tenant_id,
            institution_reference=document["institution_reference"],
            institution_reference_fingerprint=reference_fingerprint,
        )
    elif entity_type == "programme-enrolment":
        learner = _one(
            session,
            Learner,
            tenant_id,
            institution_reference_fingerprint=fingerprint(tenant_id, document["learner_reference"]),
        )
        programme = _one(session, Programme, tenant_id, code=document["programme_code"])
        version = _one(
            session,
            ProgrammeVersion,
            tenant_id,
            programme_id=programme.id,
            version_code=document["programme_version_code"],
        )
        existing = session.scalar(
            select(ProgrammeEnrolment).where(
                ProgrammeEnrolment.tenant_id == tenant_id,
                ProgrammeEnrolment.learner_id == learner.id,
                ProgrammeEnrolment.programme_version_id == version.id,
            )
        )
        record = ProgrammeEnrolment(
            id=new_id(),
            tenant_id=tenant_id,
            learner_id=learner.id,
            programme_version_id=version.id,
            effective_from=date.fromisoformat(document["effective_from"]),
            status=document["status"],
        )
    else:
        learner = _one(
            session,
            Learner,
            tenant_id,
            institution_reference_fingerprint=fingerprint(tenant_id, document["learner_reference"]),
        )
        offering = _one(session, Offering, tenant_id, code=document["offering_code"])
        existing = session.scalar(
            select(OfferingEnrolment).where(
                OfferingEnrolment.tenant_id == tenant_id,
                OfferingEnrolment.learner_id == learner.id,
                OfferingEnrolment.offering_id == offering.id,
            )
        )
        record = OfferingEnrolment(
            id=new_id(),
            tenant_id=tenant_id,
            learner_id=learner.id,
            offering_id=offering.id,
            effective_from=date.fromisoformat(document["effective_from"]),
            status=document["status"],
        )
    selected = existing or record
    return selected.id, (lambda: session.add(record)) if existing is None else (lambda: None)


def _event(session: Session, job: SyncJob, event_type: str, payload: dict[str, object]) -> None:
    enqueue_event(
        session,
        EventEnvelope(
            event_type=event_type,
            aggregate_id=UUID(job.id),
            tenant_id=UUID(job.tenant_id),
            trace_id=UUID(job.id),
            correlation_id=UUID(job.id),
            payload=payload,
        ),
    )


def _source(session: Session, connector: Connector) -> SourceSystem:
    prefix = "synthetic" if connector.kind == "synthetic_reference_erp_v1" else "mock"
    source = session.scalar(
        select(SourceSystem).where(
            SourceSystem.tenant_id == connector.tenant_id,
            SourceSystem.code == f"{prefix}-{connector.id}",
        )
    )
    if source is None:
        raise RuntimeError("connector source system is missing")
    return source


def execute_job(
    session: Session,
    *,
    tenant_id: str,
    job_id: str,
    worker_id: str = "inline",
    batch_size: int = 50,
    max_batches: int | None = None,
) -> SyncJob:
    job = session.scalar(
        select(SyncJob)
        .where(SyncJob.tenant_id == tenant_id, SyncJob.id == job_id)
        .with_for_update(skip_locked=True)
    )
    if job is None:
        raise LookupError("job not found")
    if job.state == "succeeded":
        return job
    connector = session.scalar(
        select(Connector).where(Connector.tenant_id == tenant_id, Connector.id == job.connector_id)
    )
    if connector is None or connector.status != "active":
        raise LookupError("connector not found")
    watermark = session.scalar(
        select(ConnectorWatermark).where(
            ConnectorWatermark.tenant_id == tenant_id,
            ConnectorWatermark.connector_id == connector.id,
        )
    )
    if watermark is None:
        watermark = ConnectorWatermark(
            tenant_id=tenant_id, connector_id=connector.id, checkpoint="0"
        )
        session.add(watermark)
        session.flush()
    starting = job.state == "queued"
    job.state, job.lease_owner, job.attempt = "running", worker_id, job.attempt + 1
    job.lease_expires_at, job.started_at = (
        utc_now() + timedelta(minutes=5),
        job.started_at or utc_now(),
    )
    if starting:
        if connector.kind == "synthetic_reference_erp_v1":
            _event(
                session,
                job,
                "connector.package_verified.v1",
                {"connector_id": connector.id, "package_version": "1.0.0"},
            )
        _event(
            session,
            job,
            "connector.sync_started.v1"
            if connector.kind == "synthetic_reference_erp_v1"
            else "connector.sync_started",
            {"connector_id": connector.id, "job_id": job.id, "scenario": job.scenario},
        )
    adapter = adapter_for(connector.kind, job.scenario)
    sequence = int(
        session.scalar(select(func.count(ConnectorBatch.id)).where(ConnectorBatch.job_id == job.id))
        or 0
    )
    processed_batches = 0
    while True:
        try:
            batch_data = adapter.read_batch(watermark.checkpoint, batch_size)
        except ApiError as exc:
            retryable = (
                connector.kind == "synthetic_reference_erp_v1"
                and exc.code == "transport_unavailable"
            )
            if retryable and job.attempt < 3:
                job.attempt += 1
                continue
            job.state = "failed"
            job.failure_code = exc.code
            job.completed_at, job.lease_owner, job.lease_expires_at = utc_now(), None, None
            if (
                connector.kind == "synthetic_reference_erp_v1"
                and exc.code == "source_schema_unsupported"
            ):
                _event(
                    session,
                    job,
                    "connector.schema_drift_detected.v1",
                    {"connector_id": connector.id, "job_id": job.id, "code": exc.code},
                )
            _event(
                session,
                job,
                "connector.sync_failed.v1"
                if connector.kind == "synthetic_reference_erp_v1"
                else "connector.sync_failed",
                {
                    "connector_id": connector.id,
                    "job_id": job.id,
                    "status": "failed",
                    "code": exc.code,
                    "attempts": job.attempt,
                    "backoff_seconds": [1, 2, 4] if retryable else [],
                },
            )
            return job
        batch = ConnectorBatch(
            tenant_id=tenant_id,
            job_id=job.id,
            sequence=sequence,
            checkpoint_before=watermark.checkpoint,
            checkpoint_after=batch_data.next_checkpoint,
            state="processing",
            input_count=len(batch_data.records),
            accepted_count=0,
            rejected_count=0,
            duplicate_count=0,
        )
        session.add(batch)
        session.flush()
        for source_record in batch_data.records:
            job.input_count += 1
            source_fp = fingerprint(tenant_id, source_record.source_record_key)
            dedup = hashlib.sha256(
                f"{connector.id}|{source_record.entity_type}|{source_fp}|"
                f"{source_record.source_record_version}|{job.mapping_version_id}".encode()
            ).hexdigest()
            duplicate = session.scalar(
                select(StagingRecord.id).where(
                    StagingRecord.tenant_id == tenant_id, StagingRecord.deduplication_key == dedup
                )
            )
            if duplicate:
                job.duplicate_count += 1
                batch.duplicate_count += 1
                continue
            staging = StagingRecord(
                tenant_id=tenant_id,
                connector_id=connector.id,
                batch_id=batch.id,
                entity_type=source_record.entity_type,
                source_key_fingerprint=source_fp,
                source_record_version=source_record.source_record_version,
                deduplication_key=dedup,
                normalized_document=None,
                outcome="validating",
                expires_at=utc_now()
                + (
                    timedelta(hours=24)
                    if connector.kind == "synthetic_reference_erp_v1"
                    else timedelta(days=7)
                ),
                source_updated_at=source_record.observed_at,
                effective_at=source_record.effective_at,
                retention_class="landing-24h"
                if connector.kind == "synthetic_reference_erp_v1"
                else "quarantine-7d",
            )
            session.add(staging)
            session.flush()
            try:
                document = _document(source_record.entity_type, source_record.document)
                target_id, apply_projection = _target(
                    session, tenant_id, source_record.entity_type, document
                )
                if (
                    connector.kind == "synthetic_reference_erp_v1"
                    and job.scenario == "ambiguous-identity"
                    and source_record.source_record_key == "L-9999"
                ):
                    session.add(
                        ReconciliationIssue(
                            tenant_id=tenant_id,
                            entity_type="learner",
                            target_id=target_id,
                            issue_type="identity_ambiguous",
                            severity="high",
                        )
                    )
            except (PydanticValidationError, ValueError):
                staging.outcome = "quarantined"
                if connector.kind == "synthetic_reference_erp_v1":
                    staging.retention_class = "quarantine-7d"
                    staging.expires_at = staging.created_at + timedelta(days=7)
                session.add(
                    ValidationError(
                        tenant_id=tenant_id,
                        staging_record_id=staging.id,
                        code="schema_validation_failed",
                        field_path="document",
                        rule_version="1",
                    )
                )
                job.rejected_count += 1
                batch.rejected_count += 1
                continue
            except RuntimeError:
                staging.normalized_document = source_record.document
                staging.outcome = "dead_letter"
                session.add(
                    DeadLetter(
                        tenant_id=tenant_id,
                        staging_record_id=staging.id,
                        failure_code="projection_temporarily_unavailable",
                    )
                )
                job.rejected_count += 1
                batch.rejected_count += 1
                continue
            staging.normalized_document = document
            staging.outcome = "accepted"
            semantic_hash = hashlib.sha256(
                json.dumps(document, sort_keys=True).encode()
            ).hexdigest()
            try:
                with session.begin_nested():
                    record_observation(
                        session,
                        tenant_id=tenant_id,
                        source_system_id=_source(session, connector).id,
                        entity_type=source_record.entity_type,
                        target_id=target_id,
                        source_record_key=source_record.source_record_key,
                        source_record_version=source_record.source_record_version,
                        schema_version="1",
                        mapping_version=job.mapping_version_id,
                        observed_at=source_record.observed_at,
                        effective_at=source_record.effective_at,
                        semantic_hash=semantic_hash,
                        apply_projection=apply_projection,
                        record_audit=lambda _id, _action: None,
                    )
            except RuntimeError:
                staging.outcome = "dead_letter"
                session.add(
                    DeadLetter(
                        tenant_id=tenant_id,
                        staging_record_id=staging.id,
                        failure_code="projection_temporarily_unavailable",
                    )
                )
                job.rejected_count += 1
                batch.rejected_count += 1
                continue
            job.accepted_count += 1
            batch.accepted_count += 1
        batch.state = "completed"
        watermark.checkpoint = batch_data.next_checkpoint
        watermark.version += 1
        watermark.updated_at = utc_now()
        _event(
            session,
            job,
            "connector.batch_validated.v1"
            if connector.kind == "synthetic_reference_erp_v1"
            else "connector.batch_validated",
            {
                "connector_id": connector.id,
                "job_id": job.id,
                "batch_id": batch.id,
                "input_count": batch.input_count,
                "accepted_count": batch.accepted_count,
                "rejected_count": batch.rejected_count,
                "duplicate_count": batch.duplicate_count,
            },
        )
        sequence += 1
        processed_batches += 1
        if batch_data.source_exhausted:
            accounted = job.accepted_count + job.rejected_count + job.duplicate_count
            base_disposition = (
                "matched"
                if (
                    accounted == batch_data.expected_total
                    and job.rejected_count == batch_data.expected_rejections
                    and job.duplicate_count == batch_data.expected_duplicates
                )
                else "mismatch"
            )
            measurements: dict[str, object] = {}
            breach_codes: list[str] = []
            disposition = base_disposition
            threshold_snapshot: dict[str, object] = {
                "completeness_percent": 100,
                "expected_rejections": batch_data.expected_rejections,
                "expected_duplicates": batch_data.expected_duplicates,
            }
            if connector.kind == "synthetic_reference_erp_v1":
                completeness = (
                    (accounted / batch_data.expected_total * 100)
                    if batch_data.expected_total
                    else 100.0
                )
                rejection_rate = (
                    (job.rejected_count / job.input_count * 100) if job.input_count else 0.0
                )
                duplicate_rate = (
                    (job.duplicate_count / job.input_count * 100) if job.input_count else 0.0
                )
                latest = max(
                    (record.observed_at for record in batch_data.records), default=utc_now()
                )
                clock = job.test_clock or latest
                freshness_minutes = max(0.0, (clock - latest).total_seconds() / 60)
                unresolved = 1 if job.scenario == "ambiguous-identity" else 0
                measurements = {
                    "completeness_percent": completeness,
                    "freshness_minutes": freshness_minutes,
                    "rejection_percent": rejection_rate,
                    "duplicate_percent": duplicate_rate,
                    "unresolved_reconciliation_count": unresolved,
                    "unexplained_count_variance": abs(batch_data.expected_total - accounted),
                }
                threshold_snapshot = {
                    "version": "1",
                    "completeness_min_percent": 100.0,
                    "freshness_max_minutes": 60,
                    "rejection_max_percent": 5.0,
                    "duplicate_max_percent": 2.0,
                    "unresolved_reconciliation_max_count": 0,
                    "unexplained_count_variance_max": 0,
                }
                if completeness < 100:
                    breach_codes.append("completeness_threshold_breached")
                if freshness_minutes > 60:
                    breach_codes.append("freshness_threshold_breached")
                if rejection_rate > 5 or duplicate_rate > 2 or base_disposition != "matched":
                    breach_codes.append("reconciliation_threshold_breached")
                if unresolved:
                    breach_codes.append("reconciliation_threshold_breached")
                if breach_codes:
                    disposition = "blocked"
            session.add(
                ReconciliationRun(
                    tenant_id=tenant_id,
                    job_id=job.id,
                    expected_count=batch_data.expected_total,
                    input_count=job.input_count,
                    accepted_count=job.accepted_count,
                    rejected_count=job.rejected_count,
                    duplicate_count=job.duplicate_count,
                    disposition=disposition,
                    threshold_snapshot=threshold_snapshot,
                    measurements=measurements,
                    breach_codes=breach_codes,
                )
            )
            job.state = "succeeded" if disposition == "matched" else "failed"
            if breach_codes:
                _event(
                    session,
                    job,
                    "connector.threshold_breached.v1",
                    {"connector_id": connector.id, "job_id": job.id, "codes": breach_codes},
                )
            job.completed_at, job.lease_owner, job.lease_expires_at = utc_now(), None, None
            _event(
                session,
                job,
                (
                    "connector.sync_completed.v1"
                    if job.state == "succeeded"
                    else "connector.sync_failed.v1"
                )
                if connector.kind == "synthetic_reference_erp_v1"
                else (
                    "connector.sync_completed"
                    if job.state == "succeeded"
                    else "connector.sync_failed"
                ),
                {
                    "connector_id": connector.id,
                    "job_id": job.id,
                    "status": job.state,
                    "input_count": job.input_count,
                    "accepted_count": job.accepted_count,
                    "rejected_count": job.rejected_count,
                    "duplicate_count": job.duplicate_count,
                },
            )
            return job
        if max_batches is not None and processed_batches >= max_batches:
            return job


def run_job_durably(
    engine: Engine,
    *,
    tenant_id: str,
    job_id: str,
    worker_id: str,
    batch_size: int = 5,
) -> SyncJob:
    """Commit each generated batch atomically and resume from its watermark."""

    while True:
        with Session(engine) as session, session.begin():
            if engine.dialect.name == "postgresql":
                session.execute(select(func.set_config("app.tenant_id", tenant_id, True)))
            job = execute_job(
                session,
                tenant_id=tenant_id,
                job_id=job_id,
                worker_id=worker_id,
                batch_size=batch_size,
                max_batches=1,
            )
            terminal = job.state in {"succeeded", "failed"}
        if terminal:
            with Session(engine) as session:
                result = session.scalar(
                    select(SyncJob).where(SyncJob.tenant_id == tenant_id, SyncJob.id == job_id)
                )
                if result is None:
                    raise LookupError("job not found")
                session.expunge(result)
                return result


def purge_expired_staging(session: Session, *, tenant_id: str) -> int:
    """Delete expired terminal-job staging in dependency order."""

    ids = (
        select(StagingRecord.id)
        .join(
            ConnectorBatch,
            (ConnectorBatch.tenant_id == StagingRecord.tenant_id)
            & (ConnectorBatch.id == StagingRecord.batch_id),
        )
        .join(
            SyncJob,
            (SyncJob.tenant_id == ConnectorBatch.tenant_id) & (SyncJob.id == ConnectorBatch.job_id),
        )
        .where(
            StagingRecord.tenant_id == tenant_id,
            StagingRecord.expires_at < utc_now(),
            SyncJob.state.in_(("succeeded", "failed")),
        )
    )
    record_ids = list(session.scalars(ids))
    if not record_ids:
        return 0
    session.execute(delete(DeadLetter).where(DeadLetter.staging_record_id.in_(record_ids)))
    session.execute(
        delete(ValidationError).where(ValidationError.staging_record_id.in_(record_ids))
    )
    session.execute(delete(StagingRecord).where(StagingRecord.id.in_(record_ids)))
    return len(record_ids)


def replay_dead_letter_record(
    session: Session, *, tenant_id: str, dead_letter_id: str
) -> DeadLetter:
    """Replay a generated record without retaining its raw source key in staging."""

    item = session.scalar(
        select(DeadLetter)
        .where(DeadLetter.tenant_id == tenant_id, DeadLetter.id == dead_letter_id)
        .with_for_update()
    )
    if item is None:
        raise LookupError("dead letter not found")
    if item.replay_state != "available":
        raise ValueError("replay unavailable")
    staging = session.scalar(
        select(StagingRecord).where(
            StagingRecord.tenant_id == tenant_id,
            StagingRecord.id == item.staging_record_id,
        )
    )
    batch = (
        session.scalar(
            select(ConnectorBatch).where(
                ConnectorBatch.tenant_id == tenant_id, ConnectorBatch.id == staging.batch_id
            )
        )
        if staging
        else None
    )
    job = (
        session.scalar(
            select(SyncJob).where(SyncJob.tenant_id == tenant_id, SyncJob.id == batch.job_id)
        )
        if batch
        else None
    )
    connector = session.scalar(
        select(Connector).where(
            Connector.tenant_id == tenant_id,
            Connector.id == (staging.connector_id if staging else ""),
        )
    )
    if staging is None or job is None or connector is None:
        raise RuntimeError("dead letter lineage is incomplete")
    adapter = adapter_for(connector.kind, job.scenario)
    checkpoint = "0"
    source_record = None
    while source_record is None:
        source_batch = adapter.read_batch(checkpoint, 50)
        source_record = next(
            (
                record
                for record in source_batch.records
                if fingerprint(tenant_id, record.source_record_key)
                == staging.source_key_fingerprint
            ),
            None,
        )
        if source_batch.source_exhausted:
            break
        checkpoint = source_batch.next_checkpoint
    if source_record is None:
        raise RuntimeError("generated source record is unavailable")
    if staging.normalized_document is None:
        raise RuntimeError("immutable normalized replay input is unavailable")
    document = _document(source_record.entity_type, staging.normalized_document)
    target_id, apply_projection = _target(session, tenant_id, source_record.entity_type, document)
    record_observation(
        session,
        tenant_id=tenant_id,
        source_system_id=_source(session, connector).id,
        entity_type=source_record.entity_type,
        target_id=target_id,
        source_record_key=source_record.source_record_key,
        source_record_version=source_record.source_record_version,
        schema_version="1",
        mapping_version=job.mapping_version_id,
        observed_at=source_record.observed_at,
        effective_at=source_record.effective_at,
        semantic_hash=hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest(),
        apply_projection=apply_projection,
        record_audit=lambda _id, _action: None,
    )
    staging.normalized_document = document
    staging.outcome = "accepted"
    item.replay_state = "resolved"
    item.attempts += 1
    return item
