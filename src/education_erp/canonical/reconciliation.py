"""Persistence service for authoritative canonical observations and lineage."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import exc, func, select
from sqlalchemy.orm import Session

from education_erp.canonical.service import fingerprint, reconcile_observation
from education_erp.errors import ApiError
from education_erp.persistence.phase3_models import (
    AcademicPeriodLineageLink,
    CourseLineageLink,
    CourseVersionLineageLink,
    LearnerLineageLink,
    OfferingEnrolmentLineageLink,
    OfferingLineageLink,
    ProgrammeEnrolmentLineageLink,
    ProgrammeLineageLink,
    ProgrammeVersionLineageLink,
    ReconciliationIssue,
    SourceAuthorityRule,
    SourceObservation,
    SourceSystem,
)

LINEAGE_MODELS: dict[str, tuple[type[Any], str]] = {
    "academic-period": (AcademicPeriodLineageLink, "academic_period_id"),
    "programme": (ProgrammeLineageLink, "programme_id"),
    "programme-version": (ProgrammeVersionLineageLink, "programme_version_id"),
    "course": (CourseLineageLink, "course_id"),
    "course-version": (CourseVersionLineageLink, "course_version_id"),
    "offering": (OfferingLineageLink, "offering_id"),
    "learner": (LearnerLineageLink, "learner_id"),
    "programme-enrolment": (
        ProgrammeEnrolmentLineageLink,
        "programme_enrolment_id",
    ),
    "offering-enrolment": (OfferingEnrolmentLineageLink, "offering_enrolment_id"),
}


@dataclass(frozen=True)
class ObservationResult:
    observation_id: str
    disposition: str
    replayed: bool
    reconciliation_issue_id: str | None = None


def record_observation(
    session: Session,
    *,
    tenant_id: str,
    source_system_id: str,
    entity_type: str,
    target_id: str,
    source_record_key: str,
    source_record_version: str,
    schema_version: str,
    mapping_version: str,
    observed_at: datetime,
    effective_at: datetime,
    semantic_hash: str,
    apply_projection: Callable[[], None],
    record_audit: Callable[[str, str], None],
) -> ObservationResult:
    """Persist an idempotent observation, lineage, and deterministic disposition."""

    configured = LINEAGE_MODELS.get(entity_type)
    if configured is None:
        raise ApiError(403, "source_not_authorized", "The entity type is not approved")
    active_source = session.scalar(
        select(SourceSystem.id).where(
            SourceSystem.id == source_system_id,
            SourceSystem.tenant_id == tenant_id,
            SourceSystem.status == "active",
        )
    )
    if active_source is None:
        raise ApiError(403, "source_not_authorized", "The source system is inactive")
    source_fingerprint = fingerprint(tenant_id, source_record_key)
    replay = session.scalar(
        select(SourceObservation).where(
            SourceObservation.tenant_id == tenant_id,
            SourceObservation.source_system_id == source_system_id,
            SourceObservation.entity_type == entity_type,
            SourceObservation.source_record_fingerprint == source_fingerprint,
            SourceObservation.source_record_version == source_record_version,
        )
    )
    if replay is not None:
        record_audit(replay.id, "replay")
        return ObservationResult(replay.id, "replay", True)

    authority = session.scalar(
        select(SourceAuthorityRule)
        .where(
            SourceAuthorityRule.tenant_id == tenant_id,
            SourceAuthorityRule.source_system_id == source_system_id,
            SourceAuthorityRule.entity_type == entity_type,
            SourceAuthorityRule.effective_from <= effective_at.date(),
            (
                (SourceAuthorityRule.effective_to.is_(None))
                | (SourceAuthorityRule.effective_to > effective_at.date())
            ),
        )
        .order_by(SourceAuthorityRule.effective_from.desc())
    )
    if authority is None:
        raise ApiError(403, "source_not_authorized", "The source is not authoritative")

    link_model, target_attribute = configured
    current = session.execute(
        select(SourceObservation, SourceAuthorityRule.authority)
        .join(
            link_model,
            link_model.source_observation_id == SourceObservation.id,
        )
        .join(
            SourceAuthorityRule,
            (SourceAuthorityRule.source_system_id == SourceObservation.source_system_id)
            & (SourceAuthorityRule.entity_type == SourceObservation.entity_type)
            & (SourceAuthorityRule.tenant_id == SourceObservation.tenant_id)
            & (SourceAuthorityRule.effective_from <= func.date(SourceObservation.effective_at))
            & (
                SourceAuthorityRule.effective_to.is_(None)
                | (SourceAuthorityRule.effective_to > func.date(SourceObservation.effective_at))
            ),
        )
        .where(
            SourceObservation.tenant_id == tenant_id,
            getattr(link_model, target_attribute) == target_id,
        )
        .order_by(SourceObservation.observed_at.desc())
        .limit(1)
    ).first()
    current_effective_at = current[0].effective_at if current else None
    if current_effective_at is not None and current_effective_at.tzinfo is None:
        current_effective_at = current_effective_at.replace(tzinfo=effective_at.tzinfo)
    disposition = reconcile_observation(
        current_hash=current[0].semantic_hash if current else None,
        current_authority=current[1] if current else None,
        incoming_hash=semantic_hash,
        incoming_authority=authority.authority,
        is_late=bool(current_effective_at and effective_at < current_effective_at),
    )
    observation = SourceObservation(
        tenant_id=tenant_id,
        source_system_id=source_system_id,
        entity_type=entity_type,
        source_record_key=source_record_key,
        source_record_fingerprint=source_fingerprint,
        source_record_version=source_record_version,
        schema_version=schema_version,
        mapping_version=mapping_version,
        observed_at=observed_at,
        effective_at=effective_at,
        semantic_hash=semantic_hash,
    )
    try:
        if session.get_bind().dialect.name == "postgresql":
            with session.begin_nested():
                session.add(observation)
                session.flush()
        else:
            session.add(observation)
            session.flush()
    except exc.IntegrityError:
        concurrent_replay = session.scalar(
            select(SourceObservation).where(
                SourceObservation.tenant_id == tenant_id,
                SourceObservation.source_system_id == source_system_id,
                SourceObservation.entity_type == entity_type,
                SourceObservation.source_record_fingerprint == source_fingerprint,
                SourceObservation.source_record_version == source_record_version,
            )
        )
        if concurrent_replay is None:
            raise
        record_audit(concurrent_replay.id, "replay")
        return ObservationResult(concurrent_replay.id, "replay", True)
    session.add(
        link_model(
            tenant_id=tenant_id,
            source_observation_id=observation.id,
            relationship=disposition,
            **{target_attribute: target_id},
        )
    )
    issue: ReconciliationIssue | None = None
    if disposition in {"create", "supersede"}:
        apply_projection()
    elif disposition == "reconcile":
        issue = ReconciliationIssue(
            tenant_id=tenant_id,
            entity_type=entity_type,
            target_id=target_id,
            issue_type="source_conflict",
            severity="high",
        )
        session.add(issue)
        session.flush()
    record_audit(observation.id, disposition)
    return ObservationResult(
        observation.id,
        disposition,
        False,
        issue.id if issue else None,
    )
