"""Phase 3 canonical education and lineage persistence models."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column

from education_erp.persistence.base import Base
from education_erp.persistence.models import new_id, utc_now


class Phase3Mutable:
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class AcademicPeriod(Phase3Mutable, Base):
    __tablename__ = "academic_periods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_academic_periods_tenant_id_id"),
        UniqueConstraint("tenant_id", "code", name="uq_academic_periods_tenant_id_code"),
        ForeignKeyConstraint(
            ["tenant_id", "parent_period_id"],
            ["academic_periods.tenant_id", "academic_periods.id"],
        ),
        CheckConstraint("ends_on >= starts_on", name="valid_interval"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False, index=True
    )
    parent_period_id: Mapped[str | None] = mapped_column(String(36))
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    period_type: Mapped[str] = mapped_column(String(24), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)


class Programme(Phase3Mutable, Base):
    __tablename__ = "programmes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_programmes_tenant_id_id"),
        UniqueConstraint("tenant_id", "code", name="uq_programmes_tenant_id_code"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)


class ProgrammeVersion(Phase3Mutable, Base):
    __tablename__ = "programme_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_programme_versions_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "programme_id",
            "version_code",
            name="uq_programme_versions_programme_version",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "programme_id"], ["programmes.tenant_id", "programmes.id"]
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from", name="valid_interval"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    programme_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)


class Course(Phase3Mutable, Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_courses_tenant_id_id"),
        UniqueConstraint("tenant_id", "code", name="uq_courses_tenant_id_code"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)


class CourseVersion(Phase3Mutable, Base):
    __tablename__ = "course_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_course_versions_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "course_id",
            "version_code",
            name="uq_course_versions_course_version",
        ),
        ForeignKeyConstraint(["tenant_id", "course_id"], ["courses.tenant_id", "courses.id"]),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from", name="valid_interval"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_value: Mapped[float | None] = mapped_column(Numeric(5, 2))
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)


class Offering(Phase3Mutable, Base):
    __tablename__ = "offerings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_offerings_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "academic_period_id",
            "code",
            name="uq_offerings_period_code",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "academic_period_id"],
            ["academic_periods.tenant_id", "academic_periods.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "course_version_id"],
            ["course_versions.tenant_id", "course_versions.id"],
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    academic_period_id: Mapped[str] = mapped_column(String(36), nullable=False)
    course_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    campus_id: Mapped[str | None] = mapped_column(String(36))
    department_id: Mapped[str | None] = mapped_column(String(36))
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)


class TeachingAssignment(Phase3Mutable, Base):
    __tablename__ = "teaching_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_teaching_assignments_tenant_id_id"),
        ForeignKeyConstraint(["tenant_id", "offering_id"], ["offerings.tenant_id", "offerings.id"]),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from", name="valid_interval"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    offering_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    role_code: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)


class Learner(Phase3Mutable, Base):
    __tablename__ = "learners"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_learners_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "institution_reference_fingerprint",
            name="uq_learners_tenant_reference",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False, index=True
    )
    institution_reference: Mapped[str] = mapped_column(String(200), nullable=False)
    institution_reference_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    platform_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    processing_restricted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    restriction_reason_code: Mapped[str | None] = mapped_column(String(64))
    retention_class: Mapped[str] = mapped_column(String(32), default="academic", nullable=False)
    deletion_eligible_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OfferingEnrolment(Phase3Mutable, Base):
    __tablename__ = "offering_enrolments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_offering_enrolments_tenant_id_id"),
        ForeignKeyConstraint(["tenant_id", "learner_id"], ["learners.tenant_id", "learners.id"]),
        ForeignKeyConstraint(["tenant_id", "offering_id"], ["offerings.tenant_id", "offerings.id"]),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from", name="valid_interval"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    learner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    offering_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)


class ProgrammeEnrolment(Phase3Mutable, Base):
    __tablename__ = "programme_enrolments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_programme_enrolments_tenant_id_id"),
        ForeignKeyConstraint(["tenant_id", "learner_id"], ["learners.tenant_id", "learners.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "programme_version_id"],
            ["programme_versions.tenant_id", "programme_versions.id"],
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from", name="valid_interval"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    learner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    programme_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)


class EnrolmentStatusHistory(Base):
    __tablename__ = "enrolment_status_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False, index=True
    )
    enrolment_type: Mapped[str] = mapped_column(String(16), nullable=False)
    enrolment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    from_status: Mapped[str] = mapped_column(String(24), nullable=False)
    to_status: Mapped[str] = mapped_column(String(24), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(40), nullable=False)
    changed_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SourceSystem(Phase3Mutable, Base):
    __tablename__ = "source_systems"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_source_systems_tenant_id_id"),
        UniqueConstraint("tenant_id", "code", name="uq_source_systems_tenant_id_code"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)


class SourceAuthorityRule(Phase3Mutable, Base):
    __tablename__ = "source_authority_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_source_authority_rules_tenant_id_id"),
        ForeignKeyConstraint(
            ["tenant_id", "source_system_id"], ["source_systems.tenant_id", "source_systems.id"]
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from", name="valid_interval"
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_system_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    authority: Mapped[str] = mapped_column(String(16), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)


class SourceObservation(Base):
    __tablename__ = "source_observations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_source_observations_tenant_id_id"),
        UniqueConstraint(
            "tenant_id",
            "source_system_id",
            "entity_type",
            "source_record_fingerprint",
            "source_record_version",
            name="uq_source_observations_source_version",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_system_id"], ["source_systems.tenant_id", "source_systems.id"]
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_system_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_record_key: Mapped[str] = mapped_column(String(200), nullable=False)
    source_record_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_version: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    mapping_version: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    semantic_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LearnerLineageLink(Base):
    __tablename__ = "learner_lineage_links"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "source_observation_id"],
            ["source_observations.tenant_id", "source_observations.id"],
        ),
        ForeignKeyConstraint(["tenant_id", "learner_id"], ["learners.tenant_id", "learners.id"]),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    learner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AcademicPeriodLineageLink(Base):
    __tablename__ = "academic_period_lineage_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    academic_period_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ProgrammeLineageLink(Base):
    __tablename__ = "programme_lineage_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    programme_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ProgrammeVersionLineageLink(Base):
    __tablename__ = "programme_version_lineage_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    programme_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CourseLineageLink(Base):
    __tablename__ = "course_lineage_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    course_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CourseVersionLineageLink(Base):
    __tablename__ = "course_version_lineage_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    course_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class OfferingLineageLink(Base):
    __tablename__ = "offering_lineage_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    offering_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ProgrammeEnrolmentLineageLink(Base):
    __tablename__ = "programme_enrolment_lineage_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    programme_enrolment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class OfferingEnrolmentLineageLink(Base):
    __tablename__ = "offering_enrolment_lineage_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_observation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    offering_enrolment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReconciliationIssue(Phase3Mutable, Base):
    __tablename__ = "reconciliation_issues"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_reconciliation_issues_tenant_id_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(36))
    issue_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="open", nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    resolution_code: Mapped[str | None] = mapped_column(String(40))
    resolved_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SubjectRightsRequest(Phase3Mutable, Base):
    __tablename__ = "subject_rights_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_subject_rights_requests_tenant_id_id"),
        ForeignKeyConstraint(["tenant_id", "learner_id"], ["learners.tenant_id", "learners.id"]),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    learner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_type: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="open", nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(40), nullable=False)
    disposition_code: Mapped[str | None] = mapped_column(String(40))
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))


class SubjectExportManifest(Base):
    __tablename__ = "subject_export_manifests"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "request_id",
            name="uq_subject_export_manifests_request",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id"), nullable=False, index=True
    )
    learner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="metadata_only", nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@event.listens_for(SourceObservation, "before_update")
@event.listens_for(SourceObservation, "before_delete")
@event.listens_for(LearnerLineageLink, "before_update")
@event.listens_for(LearnerLineageLink, "before_delete")
@event.listens_for(AcademicPeriodLineageLink, "before_update")
@event.listens_for(AcademicPeriodLineageLink, "before_delete")
@event.listens_for(ProgrammeLineageLink, "before_update")
@event.listens_for(ProgrammeLineageLink, "before_delete")
@event.listens_for(ProgrammeVersionLineageLink, "before_update")
@event.listens_for(ProgrammeVersionLineageLink, "before_delete")
@event.listens_for(CourseLineageLink, "before_update")
@event.listens_for(CourseLineageLink, "before_delete")
@event.listens_for(CourseVersionLineageLink, "before_update")
@event.listens_for(CourseVersionLineageLink, "before_delete")
@event.listens_for(OfferingLineageLink, "before_update")
@event.listens_for(OfferingLineageLink, "before_delete")
@event.listens_for(ProgrammeEnrolmentLineageLink, "before_update")
@event.listens_for(ProgrammeEnrolmentLineageLink, "before_delete")
@event.listens_for(OfferingEnrolmentLineageLink, "before_update")
@event.listens_for(OfferingEnrolmentLineageLink, "before_delete")
@event.listens_for(EnrolmentStatusHistory, "before_update")
@event.listens_for(EnrolmentStatusHistory, "before_delete")
@event.listens_for(SubjectExportManifest, "before_update")
@event.listens_for(SubjectExportManifest, "before_delete")
def prevent_phase3_history_mutation(*_: object) -> None:
    raise ValueError("phase 3 history is immutable")
