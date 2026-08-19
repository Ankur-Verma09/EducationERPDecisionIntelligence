# Phase 3 Low-Level Design

Status: Approved baseline  
Date: 2026-07-29

## Package layout

```text
src/education_erp/
├── academics/
│   ├── domain.py
│   ├── repository.py
│   └── service.py
├── learners/
│   ├── domain.py
│   ├── repository.py
│   └── service.py
├── enrolments/
│   ├── domain.py
│   ├── repository.py
│   └── service.py
├── lineage/
│   ├── domain.py
│   ├── ports.py
│   ├── repository.py
│   └── service.py
├── privacy/
│   ├── domain.py
│   └── service.py
├── api/
│   └── phase3.py
└── persistence/
    └── phase3_models.py
```

Existing Phase 2 identity, authorization, audit, idempotency, cursor, error, and
tenant-context components are reused. Phase 3 may refactor shared helpers without
changing their contracts.

## Domain types

```text
TenantOwnedId = UUID
CanonicalStatus = active | inactive | retired
EnrolmentStatus = pending | active | suspended | withdrawn | completed | cancelled
SourceAuthority = primary | secondary | reference
ReconciliationStatus = open | resolved | dismissed
SubjectRequestType = access | correction | restriction | deletion
```

Codes and references use validated value objects. Dates are timezone-independent
business dates; observations and audit use timezone-aware UTC timestamps.

## Repository contracts

Every repository is constructed with an immutable `TenantContext` and a SQLAlchemy
session whose transaction has `app.tenant_id` set. Repository methods do not accept
arbitrary tenant IDs.

```text
AcademicRepository
  create_period, update_period, get_period, list_periods
  create_programme, add_programme_version
  create_course, add_course_version
  create_offering, update_offering

LearnerRepository
  create, get, list, restrict_processing, retire
  find_by_protected_reference

EnrolmentRepository
  create, transition, list_for_learner, list_for_offering

LineageRepository
  register_source, append_observation, link, supersede
  get_record_lineage

ReconciliationRepository
  open_issue, resolve_issue, list_issues
```

All list methods use a stable UUID boundary and bounded limit. No repository returns
unmasked identifiers unless its method is explicitly protected.

## Service authorization

```text
authorize_education(context, permission, resource_scope):
    require active tenant and membership
    require permission from approved Phase 3 role mapping
    require resource campus/department within assignment scope
    require MFA/reason for protected identifier, export, lineage mutation,
        or reconciliation resolution
    require record not processing-restricted unless subject_rights permission
```

Platform roles confer no access. Teaching assignments are data only.

## Aggregate rules

### Academic periods

- end date is on or after start date;
- child period lies wholly within its parent;
- no parent cycle;
- code unique per tenant;
- closed periods cannot receive new active offerings without an explicit,
  audited registrar override (override is deferred unless contract includes it).

### Programme/course versions

- stable root record plus effective-dated versions;
- intervals for one root cannot overlap;
- prior versions are immutable after supersession;
- retirement prevents new offerings/enrolments but preserves history.

### Offerings

- reference one course version and academic period in the same tenant;
- optional campus and department must be tenant-consistent and mutually consistent;
- code unique per tenant and academic period;
- department scope is derived from the offering, never caller-asserted.

### Learners

- tenant-local generated canonical ID;
- protected institutional reference unique within tenant;
- optional Phase 2 user link is tenant-consistent through active/known membership
  policy but grants no authorization;
- restriction blocks ordinary mutation and future processing;
- merge never crosses tenants and preserves both source histories.

### Enrolments

- learner and target share tenant;
- programme/offering interval must overlap enrolment effective interval;
- one overlapping active enrolment per learner and target;
- transitions are explicit and audited;
- correction creates a version, not an in-place history rewrite.

## Observation matching algorithm

```text
accept(observation):
    require registered active source
    require source authorized for entity_type
    normalize and hash allowlisted semantic values
    append immutable observation
    candidate = match tenant-local canonical stable key
    if no candidate:
        create canonical projection when policy permits
    elif semantic hash equals current:
        add lineage link only
    elif source outranks current authority deterministically:
        create new canonical version and supersession link
    else:
        open reconciliation issue
```

The source key and semantic hash are protected metadata. Idempotency uniqueness is
`(tenant_id, source_system_id, entity_type, source_record_key, observed_version)`.

## Merge and split

- automatic learner merge is prohibited;
- an authorized registrar may propose a tenant-local merge;
- resolution requires MFA, reason, optimistic concurrency, and audit;
- the surviving learner receives lineage aliases; the retired learner remains as a
  tombstone and cannot be reused;
- splitting a prior merge is a separate audited operation and restores associations
  from immutable history;
- first-release public API does not expose merge/split until separately approved.

## Transactions and audit

Canonical mutation, lineage link, reconciliation state, and audit event commit in one
transaction. Observation append is immutable. If projection fails, the observation
and a reconciliation issue may commit together only through the internal observation
service; API mutations fail atomically.

Audit changes contain field names and canonical IDs, not protected values. Sensitive
read audit records reason, target canonical ID, actor, permission, and request ID.

## Concurrency and idempotency

- all mutations require `Idempotency-Key`;
- mutable resources return weak ETags from integer versions;
- `If-Match` is required for PATCH, transitions, restriction, and reconciliation;
- uniqueness and exclusion constraints provide race safety;
- one idempotency record is stored per concrete actor/tenant/method/route/key.

## Validation and errors

Pydantic request models use `extra="forbid"`, bounded strings, closed enums, and
date/relationship validators. Standard errors are extended with:

- `prohibited_attribute`
- `processing_restricted`
- `reconciliation_required`
- `source_not_authorized`
- `temporal_conflict`

Errors never reveal foreign-tenant existence, source keys, institutional references,
or conflicting values.

## Implementation sequencing

Models and migration precede repositories; repositories precede services; services
precede APIs. Each vertical slice includes domain tests, PostgreSQL constraint/RLS
tests, API/security tests where exposed, and traceability updates.
