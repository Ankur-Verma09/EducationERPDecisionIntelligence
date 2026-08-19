from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from education_erp.canonical.reconciliation import LINEAGE_MODELS, record_observation
from education_erp.errors import ApiError
from education_erp.persistence.base import Base
from education_erp.persistence.phase3_models import (
    SourceAuthorityRule,
    SourceObservation,
    SourceSystem,
)


def _record(
    session: Session,
    *,
    source_system_id: str,
    version: str,
    semantic_hash: str,
    observed_at: datetime,
    applied: list[str],
):
    return record_observation(
        session,
        tenant_id="tenant-a",
        source_system_id=source_system_id,
        entity_type="learner",
        target_id="learner-a",
        source_record_key="GENERATED-KEY",
        source_record_version=version,
        schema_version="1",
        mapping_version="map-1",
        observed_at=observed_at,
        effective_at=observed_at,
        semantic_hash=semantic_hash,
        apply_projection=lambda: applied.append(version),
        record_audit=lambda _observation_id, _disposition: None,
    )


def test_observation_service_persists_replay_precedence_and_conflict() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime(2026, 7, 1, tzinfo=UTC)
    with Session(engine) as session:
        session.add_all(
            [
                SourceSystem(
                    id="source-secondary",
                    tenant_id="tenant-a",
                    code="SECONDARY",
                    display_name="Generated secondary",
                ),
                SourceSystem(
                    id="source-primary",
                    tenant_id="tenant-a",
                    code="PRIMARY",
                    display_name="Generated primary",
                ),
                SourceAuthorityRule(
                    tenant_id="tenant-a",
                    source_system_id="source-secondary",
                    entity_type="learner",
                    authority="secondary",
                    effective_from=date(2026, 1, 1),
                ),
                SourceAuthorityRule(
                    tenant_id="tenant-a",
                    source_system_id="source-primary",
                    entity_type="learner",
                    authority="primary",
                    effective_from=date(2026, 1, 1),
                ),
            ]
        )
        session.flush()
        applied: list[str] = []

        created = _record(
            session,
            source_system_id="source-secondary",
            version="1",
            semantic_hash="hash-a",
            observed_at=now,
            applied=applied,
        )
        replayed = _record(
            session,
            source_system_id="source-secondary",
            version="1",
            semantic_hash="hash-a",
            observed_at=now,
            applied=applied,
        )
        superseded = _record(
            session,
            source_system_id="source-primary",
            version="2",
            semantic_hash="hash-b",
            observed_at=now + timedelta(hours=1),
            applied=applied,
        )
        conflict = _record(
            session,
            source_system_id="source-secondary",
            version="3",
            semantic_hash="hash-c",
            observed_at=now + timedelta(hours=2),
            applied=applied,
        )

        assert created.disposition == "create"
        assert replayed.replayed is True
        assert superseded.disposition == "supersede"
        assert conflict.disposition == "reconcile"
        assert conflict.reconciliation_issue_id is not None
        assert applied == ["1", "2"]


def test_observation_service_rejects_unapproved_entity_and_source() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        values = dict(
            session=session,
            tenant_id="tenant-a",
            source_system_id="source",
            target_id="target",
            source_record_key="GENERATED",
            source_record_version="1",
            schema_version="1",
            mapping_version="1",
            observed_at=datetime(2026, 7, 1, tzinfo=UTC),
            effective_at=datetime(2026, 7, 1, tzinfo=UTC),
            semantic_hash="hash",
            apply_projection=lambda: None,
            record_audit=lambda _observation_id, _disposition: None,
        )
        with pytest.raises(ApiError, match="entity type"):
            record_observation(entity_type="unknown", **values)
        with pytest.raises(ApiError, match="inactive"):
            record_observation(entity_type="learner", **values)


def test_all_approved_entities_have_application_lineage_models() -> None:
    assert set(LINEAGE_MODELS) == {
        "academic-period",
        "programme",
        "programme-version",
        "course",
        "course-version",
        "offering",
        "learner",
        "programme-enrolment",
        "offering-enrolment",
    }

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            SourceSystem(
                id="source-primary",
                tenant_id="tenant-a",
                code="PRIMARY",
                display_name="Generated primary",
            )
        )
        for entity_type in LINEAGE_MODELS:
            session.add(
                SourceAuthorityRule(
                    tenant_id="tenant-a",
                    source_system_id="source-primary",
                    entity_type=entity_type,
                    authority="primary",
                    effective_from=date(2026, 1, 1),
                )
            )
        session.flush()
        for index, (entity_type, (link_model, target_attribute)) in enumerate(
            LINEAGE_MODELS.items()
        ):
            result = record_observation(
                session,
                tenant_id="tenant-a",
                source_system_id="source-primary",
                entity_type=entity_type,
                target_id=f"target-{index}",
                source_record_key=f"GENERATED-{index}",
                source_record_version="1",
                schema_version="1",
                mapping_version="1",
                observed_at=datetime(2026, 7, 1, tzinfo=UTC),
                effective_at=datetime(2026, 7, 1, tzinfo=UTC),
                semantic_hash=f"hash-{index}",
                apply_projection=lambda: None,
                record_audit=lambda _observation_id, _disposition: None,
            )
            assert result.disposition == "create"
            link = session.scalar(select(link_model))
            assert getattr(link, target_attribute) == f"target-{index}"


def test_adversarial_source_key_is_treated_as_opaque_data() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            SourceSystem(
                id="source",
                tenant_id="tenant-a",
                code="SOURCE",
                display_name="Generated source",
            )
        )
        session.add(
            SourceAuthorityRule(
                tenant_id="tenant-a",
                source_system_id="source",
                entity_type="learner",
                authority="primary",
                effective_from=date(2026, 1, 1),
            )
        )
        session.flush()
        hostile = "../../records/' OR 1=1 --"
        record_observation(
            session,
            tenant_id="tenant-a",
            source_system_id="source",
            entity_type="learner",
            target_id="target",
            source_record_key=hostile,
            source_record_version="1",
            schema_version="1",
            mapping_version="1",
            observed_at=datetime(2026, 7, 1, tzinfo=UTC),
            effective_at=datetime(2026, 7, 1, tzinfo=UTC),
            semantic_hash="hash",
            apply_projection=lambda: None,
            record_audit=lambda _observation_id, _disposition: None,
        )
        observation = session.scalar(select(SourceObservation))
        assert observation is not None
        assert observation.source_record_key == hostile


def test_observation_audit_failure_rolls_back_atomic_transaction() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            SourceSystem(
                id="source",
                tenant_id="tenant-a",
                code="SOURCE",
                display_name="Generated source",
            )
        )
        session.add(
            SourceAuthorityRule(
                tenant_id="tenant-a",
                source_system_id="source",
                entity_type="learner",
                authority="primary",
                effective_from=date(2026, 1, 1),
            )
        )
        session.commit()

        def fail_audit(_observation_id: str, _disposition: str) -> None:
            raise RuntimeError("audit unavailable")

        with pytest.raises(RuntimeError, match="audit unavailable"), session.begin():
            record_observation(
                session,
                tenant_id="tenant-a",
                source_system_id="source",
                entity_type="learner",
                target_id="target",
                source_record_key="GENERATED",
                source_record_version="1",
                schema_version="1",
                mapping_version="1",
                observed_at=datetime(2026, 7, 1, tzinfo=UTC),
                effective_at=datetime(2026, 7, 1, tzinfo=UTC),
                semantic_hash="hash",
                apply_projection=lambda: None,
                record_audit=fail_audit,
            )
        assert session.scalar(select(SourceObservation)) is None
