import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, exc, func, select, text
from sqlalchemy.orm import Session

from education_erp.canonical.reconciliation import LINEAGE_MODELS, record_observation
from education_erp.persistence.models import AuditEvent, Institution
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
    SourceAuthorityRule,
    SourceSystem,
)


@pytest.mark.integration
def test_phase3_postgresql_tables_force_rls_and_runtime_cannot_bypass() -> None:
    owner_url = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    runtime_url = os.getenv("EDUERP_TEST_DATABASE_URL")
    if not owner_url or not runtime_url:
        pytest.skip("PostgreSQL runtime and migration URLs are required")

    owner = create_engine(owner_url)
    runtime = create_engine(runtime_url)
    with owner.connect() as connection:
        forced = connection.execute(
            text(
                "SELECT count(*) FROM pg_class "
                "WHERE relname IN ('learners','academic_periods','offering_enrolments',"
                "'source_observations') AND relrowsecurity AND relforcerowsecurity"
            )
        ).scalar_one()
        assert forced == 4
        lineage_tables = connection.execute(
            text(
                "SELECT count(*) FROM pg_class WHERE relname LIKE '%_lineage_links' "
                "AND relrowsecurity AND relforcerowsecurity"
            )
        ).scalar_one()
        assert lineage_tables == 9
        exclusion_constraints = connection.execute(
            text(
                "SELECT count(*) FROM pg_constraint "
                "WHERE conname IN ('ex_programme_versions_effective',"
                "'ex_course_versions_effective','ex_programme_enrolments_effective',"
                "'ex_offering_enrolments_effective') AND contype = 'x'"
            )
        ).scalar_one()
        assert exclusion_constraints == 4
        immutable_triggers = connection.execute(
            text(
                "SELECT count(*) FROM pg_trigger WHERE tgname LIKE '%_immutable' "
                "AND NOT tgisinternal"
            )
        ).scalar_one()
        assert immutable_triggers >= 12
        effective_time_column = connection.execute(
            text(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_name = 'source_observations' "
                "AND column_name = 'effective_at' AND is_nullable = 'NO'"
            )
        ).scalar_one()
        assert effective_time_column == 1
        observation_replay_constraint = connection.execute(
            text(
                "SELECT count(*) FROM pg_constraint "
                "WHERE conname = 'uq_source_observations_source_version'"
            )
        ).scalar_one()
        assert observation_replay_constraint == 1
    with runtime.connect() as connection:
        role = connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        ).one()
        assert role == (False, False)
        assert connection.execute(text("SELECT count(*) FROM learners")).scalar_one() == 0
        assert (
            connection.execute(
                text("SELECT has_table_privilege(current_user, 'source_observations', 'UPDATE')")
            ).scalar_one()
            is False
        )
    owner.dispose()
    runtime.dispose()


@pytest.mark.integration
def test_phase3_postgresql_observation_replay_is_uniquely_enforced() -> None:
    owner_url = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    if not owner_url:
        pytest.skip("PostgreSQL migration URL is required")
    engine = create_engine(owner_url)
    tenant_id, source_id = str(uuid4()), str(uuid4())
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO institutions "
                "(id,slug,legal_name,display_name,status,data_region,security_epoch,"
                "version,created_at,updated_at) VALUES "
                "(:id,:slug,'Generated','Generated','active','test',0,1,now(),now())"
            ),
            {"id": tenant_id, "slug": f"generated-{tenant_id}"},
        )
        connection.execute(
            text(
                "INSERT INTO source_systems "
                "(id,tenant_id,code,display_name,status,version,created_at,updated_at) "
                "VALUES (:id,:tenant,'GEN','Generated','active',1,now(),now())"
            ),
            {"id": source_id, "tenant": tenant_id},
        )
        statement = text(
            "INSERT INTO source_observations "
            "(id,tenant_id,source_system_id,entity_type,source_record_key,"
            "source_record_fingerprint,source_record_version,schema_version,"
            "mapping_version,observed_at,effective_at,semantic_hash,created_at) "
            "VALUES (:id,:tenant,:source,'learner','GENERATED','fingerprint','1',"
            "'1','1',now(),now(),'hash',now())"
        )
        connection.execute(
            statement,
            {"id": str(uuid4()), "tenant": tenant_id, "source": source_id},
        )
        savepoint = connection.begin_nested()
        with pytest.raises(exc.IntegrityError):
            connection.execute(
                statement,
                {"id": str(uuid4()), "tenant": tenant_id, "source": source_id},
            )
        savepoint.rollback()
    engine.dispose()


@pytest.mark.integration
def test_phase3_postgresql_rejects_overlapping_temporal_versions() -> None:
    owner_url = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    if not owner_url:
        pytest.skip("PostgreSQL migration URL is required")
    engine = create_engine(owner_url)
    tenant_id, programme_id = str(uuid4()), str(uuid4())
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO institutions "
                "(id,slug,legal_name,display_name,status,data_region,security_epoch,"
                "version,created_at,updated_at) VALUES "
                "(:id,:slug,'Generated','Generated','active','test',0,1,now(),now())"
            ),
            {"id": tenant_id, "slug": f"generated-overlap-{tenant_id}"},
        )
        connection.execute(
            text(
                "INSERT INTO programmes "
                "(id,tenant_id,code,status,version,created_at,updated_at) "
                "VALUES (:id,:tenant,'GEN','active',1,now(),now())"
            ),
            {"id": programme_id, "tenant": tenant_id},
        )
        statement = text(
            "INSERT INTO programme_versions "
            "(id,tenant_id,programme_id,version_code,name,effective_from,effective_to,"
            "status,version,created_at,updated_at) VALUES "
            "(:id,:tenant,:programme,:code,'Generated',:starts,:ends,"
            "'active',1,now(),now())"
        )
        connection.execute(
            statement,
            {
                "id": str(uuid4()),
                "tenant": tenant_id,
                "programme": programme_id,
                "code": "V1",
                "starts": "2026-01-01",
                "ends": "2026-12-31",
            },
        )
        savepoint = connection.begin_nested()
        with pytest.raises(exc.IntegrityError):
            connection.execute(
                statement,
                {
                    "id": str(uuid4()),
                    "tenant": tenant_id,
                    "programme": programme_id,
                    "code": "V2",
                    "starts": "2026-06-01",
                    "ends": "2027-01-01",
                },
            )
        savepoint.rollback()
    engine.dispose()


@pytest.mark.integration
def test_phase3_postgresql_persists_all_entity_lineage_projection_and_audit() -> None:
    owner_url = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    if not owner_url:
        pytest.skip("PostgreSQL migration URL is required")
    engine = create_engine(owner_url)
    tenant_id = str(uuid4())
    with Session(engine) as session, session.begin():
        session.add(
            Institution(
                id=tenant_id,
                slug=f"generated-lineage-{tenant_id}",
                legal_name="Generated",
                display_name="Generated",
                status="active",
                data_region="test",
            )
        )
        session.flush()
        session.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": tenant_id},
        )
        period = AcademicPeriod(
            tenant_id=tenant_id,
            code="P1",
            name="Generated",
            period_type="term",
            starts_on=date(2026, 1, 1),
            ends_on=date(2026, 12, 31),
        )
        programme = Programme(tenant_id=tenant_id, code="PROGRAMME")
        course = Course(tenant_id=tenant_id, code="COURSE")
        learner = Learner(
            tenant_id=tenant_id,
            institution_reference="GEN-LRN",
            institution_reference_fingerprint="generated-fingerprint",
        )
        source = SourceSystem(
            tenant_id=tenant_id,
            code="SOURCE",
            display_name="Generated",
        )
        session.add_all([period, programme, course, learner, source])
        session.flush()
        programme_version = ProgrammeVersion(
            tenant_id=tenant_id,
            programme_id=programme.id,
            version_code="V1",
            name="Generated",
            effective_from=date(2026, 1, 1),
        )
        course_version = CourseVersion(
            tenant_id=tenant_id,
            course_id=course.id,
            version_code="V1",
            title="Generated",
            effective_from=date(2026, 1, 1),
        )
        session.add_all([programme_version, course_version])
        session.flush()
        offering = Offering(
            tenant_id=tenant_id,
            academic_period_id=period.id,
            course_version_id=course_version.id,
            code="OFFERING",
        )
        programme_enrolment = ProgrammeEnrolment(
            tenant_id=tenant_id,
            learner_id=learner.id,
            programme_version_id=programme_version.id,
            effective_from=date(2026, 1, 1),
        )
        session.add_all([offering, programme_enrolment])
        session.flush()
        offering_enrolment = OfferingEnrolment(
            tenant_id=tenant_id,
            learner_id=learner.id,
            offering_id=offering.id,
            effective_from=date(2026, 1, 1),
        )
        session.add(offering_enrolment)
        session.flush()
        targets = {
            "academic-period": period.id,
            "programme": programme.id,
            "programme-version": programme_version.id,
            "course": course.id,
            "course-version": course_version.id,
            "offering": offering.id,
            "learner": learner.id,
            "programme-enrolment": programme_enrolment.id,
            "offering-enrolment": offering_enrolment.id,
        }
        for entity_type in targets:
            session.add(
                SourceAuthorityRule(
                    tenant_id=tenant_id,
                    source_system_id=source.id,
                    entity_type=entity_type,
                    authority="primary",
                    effective_from=date(2026, 1, 1),
                )
            )
        session.flush()
        projected: list[str] = []
        for entity_type, target_id in targets.items():
            result = record_observation(
                session,
                tenant_id=tenant_id,
                source_system_id=source.id,
                entity_type=entity_type,
                target_id=target_id,
                source_record_key=f"GENERATED-{entity_type}",
                source_record_version="1",
                schema_version="1",
                mapping_version="1",
                observed_at=datetime(2026, 7, 1, tzinfo=UTC),
                effective_at=datetime(2026, 1, 1, tzinfo=UTC),
                semantic_hash=f"hash-{entity_type}",
                apply_projection=lambda kind=entity_type: projected.append(kind),
                record_audit=lambda observation_id, disposition: session.add(
                    AuditEvent(
                        tenant_id=tenant_id,
                        actor_user_id=None,
                        action=f"observation.{disposition}",
                        target_type="source_observation",
                        target_id=observation_id,
                        outcome="success",
                        request_id=str(uuid4()),
                        reason="generated reconciliation",
                    )
                ),
            )
            assert result.disposition == "create"
        session.flush()
        assert set(projected) == set(targets)
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(
                    AuditEvent.tenant_id == tenant_id,
                    AuditEvent.action == "observation.create",
                )
            )
            == 9
        )
        for link_model, _target_attribute in LINEAGE_MODELS.values():
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(link_model)
                    .where(link_model.tenant_id == tenant_id)
                )
                == 1
            )
    engine.dispose()


@pytest.mark.integration
def test_phase3_postgresql_record_observation_race_replays_one_result() -> None:
    owner_url = os.getenv("EDUERP_MIGRATION_DATABASE_URL")
    if not owner_url:
        pytest.skip("PostgreSQL migration URL is required")
    engine = create_engine(owner_url)
    tenant_id = str(uuid4())
    with Session(engine) as session, session.begin():
        session.add(
            Institution(
                id=tenant_id,
                slug=f"generated-race-{tenant_id}",
                legal_name="Generated",
                display_name="Generated",
                status="active",
                data_region="test",
            )
        )
        session.flush()
        session.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": tenant_id},
        )
        source = SourceSystem(
            tenant_id=tenant_id,
            code="SOURCE",
            display_name="Generated",
        )
        learner = Learner(
            tenant_id=tenant_id,
            institution_reference="GEN-RACE",
            institution_reference_fingerprint="generated-race-fingerprint",
        )
        session.add_all([source, learner])
        session.flush()
        session.add(
            SourceAuthorityRule(
                tenant_id=tenant_id,
                source_system_id=source.id,
                entity_type="learner",
                authority="primary",
                effective_from=date(2026, 1, 1),
            )
        )
        session.flush()
        source_id, learner_id = source.id, learner.id

    barrier = Barrier(2)

    def submit() -> tuple[str, bool]:
        with Session(engine) as session, session.begin():
            session.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": tenant_id},
            )
            barrier.wait()
            result = record_observation(
                session,
                tenant_id=tenant_id,
                source_system_id=source_id,
                entity_type="learner",
                target_id=learner_id,
                source_record_key="GENERATED-RACE",
                source_record_version="1",
                schema_version="1",
                mapping_version="1",
                observed_at=datetime(2026, 7, 1, tzinfo=UTC),
                effective_at=datetime(2026, 1, 1, tzinfo=UTC),
                semantic_hash="generated-race-hash",
                apply_projection=lambda: None,
                record_audit=lambda _observation_id, _disposition: None,
            )
            return result.observation_id, result.replayed

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: submit(), range(2)))
    assert results[0][0] == results[1][0]
    assert sorted(replayed for _observation_id, replayed in results) == [False, True]
    engine.dispose()
