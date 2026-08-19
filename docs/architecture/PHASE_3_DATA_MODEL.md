# Phase 3 Data Model

Status: Approved baseline  
Date: 2026-07-29

All primary IDs are UUIDs. Every Phase 3 business table contains immutable
`tenant_id`. All timestamps are timezone-aware UTC; effective business dates use
PostgreSQL `date`. Mutable aggregates contain integer `version`, `created_at`, and
`updated_at`. Every tenant-owned table enables and forces RLS.

## Academic structure

### `academic_periods`

- `id`, `tenant_id`
- optional `parent_period_id`
- `code`, `name`, `period_type`
- `starts_on`, `ends_on`, `status`
- version/timestamps

Constraints: tenant/code unique; composite parent tenant FK; valid date interval;
parent containment enforced by service plus integration tests.

### `programmes`

- `id`, `tenant_id`
- `code`, `status`
- version/timestamps

### `programme_versions`

- `id`, `tenant_id`, `programme_id`
- `version_code`, `name`
- `effective_from`, optional `effective_to`
- `status`, version/timestamps

Constraints: tenant-consistent programme FK; unique version code per programme;
non-empty interval; PostgreSQL exclusion constraint prevents overlapping active
effective intervals.

### `courses`

- `id`, `tenant_id`
- `code`, `status`
- version/timestamps

### `course_versions`

- `id`, `tenant_id`, `course_id`
- `version_code`, `title`
- optional numeric `credit_value`
- `effective_from`, optional `effective_to`
- `status`, version/timestamps

Constraints mirror programme versions.

### `offerings`

- `id`, `tenant_id`
- `academic_period_id`, `course_version_id`
- optional `campus_id`, optional `department_id`
- `code`, `status`
- version/timestamps

Constraints: all composite tenant FKs; department/campus consistency; unique
`(tenant_id, academic_period_id, code)`.

### `teaching_assignments`

- `id`, `tenant_id`, `offering_id`, `user_id`
- `role_code`
- `effective_from`, optional `effective_to`
- version/timestamps

Teaching assignments are descriptive and never authorization grants.

## Learners and enrolments

### `learners`

- `id`, `tenant_id`
- encrypted/tokenized `institution_reference`
- `institution_reference_fingerprint` for tenant-local uniqueness/search
- optional `platform_user_id`
- `status`
- `processing_restricted`, optional `restriction_reason_code`
- `retention_class`, optional `deletion_eligible_at`
- version/timestamps

No name, date of birth, contact, demographic, guardian, health, discipline, or
free-form notes.

### `programme_enrolments`

- `id`, `tenant_id`, `learner_id`, `programme_version_id`
- `status`, `effective_from`, optional `effective_to`
- version/timestamps

### `offering_enrolments`

- `id`, `tenant_id`, `learner_id`, `offering_id`
- `status`, `effective_from`, optional `effective_to`
- version/timestamps

Both use composite tenant FKs, valid intervals, and exclusion constraints preventing
overlapping active enrolments for the same learner/target.

### `enrolment_status_history`

- `id`, `tenant_id`
- exactly one of `programme_enrolment_id`, `offering_enrolment_id`
- `from_status`, `to_status`, `effective_at`
- `reason_code`, `changed_by_user_id`, `created_at`

Append-only. No free-form reason.

## Source authority and lineage

### `source_systems`

- `id`, `tenant_id`
- `code`, `display_name`, `status`
- version/timestamps

No credentials or endpoint secrets.

### `source_authority_rules`

- `id`, `tenant_id`, `source_system_id`
- `entity_type`, `authority` (`primary`, `secondary`, `reference`)
- effective interval
- version/timestamps

At most one active primary source per tenant/entity type.

### `source_observations`

- `id`, `tenant_id`, `source_system_id`
- `entity_type`
- protected `source_record_key`
- `source_record_fingerprint`
- `source_record_version`
- `schema_version`, `mapping_version`
- `observed_at`, optional `effective_from`, optional `effective_to`
- `semantic_hash`
- optional `supersedes_observation_id`
- `created_at`

Immutable; contains no raw payload and no arbitrary JSON.

### Concrete lineage link tables

Use one link table per canonical target type:

- `academic_period_lineage_links`
- `programme_lineage_links`
- `programme_version_lineage_links`
- `course_lineage_links`
- `course_version_lineage_links`
- `offering_lineage_links`
- `learner_lineage_links`
- `programme_enrolment_lineage_links`
- `offering_enrolment_lineage_links`

Each contains `id`, `tenant_id`, `source_observation_id`, the concrete canonical
target ID, `relationship`, and `created_at`. Both observation and target use
composite tenant foreign keys. `relationship` is one of `created`, `confirmed`,
`corrected`, `superseded`, or `merged_alias`.

Concrete tables are deliberately repetitive: PostgreSQL can enforce target existence
and tenant consistency without unchecked polymorphic IDs or triggers.

### `reconciliation_issues`

- `id`, `tenant_id`
- `entity_type`
- optional canonical target
- `issue_type`, `status`, `severity`
- conflicting observation IDs through join table
- `resolution_code`, optional `resolved_by_user_id`, `resolved_at`
- version/timestamps

No conflicting values or raw payload in the issue.

### `reconciliation_issue_observations`

- `tenant_id`, `issue_id`, `observation_id`
- composite tenant FKs

## Privacy operations

### `subject_rights_requests`

- `id`, `tenant_id`, `learner_id`
- `request_type`, `status`
- `received_at`, `due_at`
- `reason_code`, optional `disposition_code`
- `created_by_user_id`, optional `completed_by_user_id`, `completed_at`
- version/timestamps

### `subject_export_manifests`

- `id`, `tenant_id`, `learner_id`, `request_id`
- `status`, `record_counts`
- `created_by_user_id`, `created_at`, `expires_at`

The database stores manifest metadata only. Any generated artifact belongs to a later
approved encrypted object-storage design.

## Tenant isolation

Every table uses:

```sql
USING (
  tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
)
WITH CHECK (
  tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
)
```

All foreign relationships use `(tenant_id, referenced_id)` composite keys. Global
users may be referenced only where application authorization proves the relationship;
such references confer no tenant access.

## Immutability

- tenant IDs never change;
- source observations, lineage links, and status history are append-only;
- source keys and institutional references are never emitted in logs/audit changes;
- correction creates versions/supersession rather than overwriting evidence;
- deletion uses tombstone/eligibility metadata in Phase 3.

## Migration requirements

- additive revision `0005`;
- preserve `0001`–`0004`;
- PostgreSQL extensions/constraints must be explicitly reversible;
- create tables before RLS policies and grants;
- downgrade policies/grants before tables;
- validate fresh, populated `0004 -> 0005`, `0005 -> 0004 -> 0005`, and full
  `0005 -> base -> 0005`;
- assert runtime role is `NOSUPERUSER NOBYPASSRLS`;
- include cross-tenant joins, pool reuse, invalid temporal ranges, overlap races,
  append-only enforcement, and populated rollback compatibility tests.
