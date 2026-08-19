# Phase 3 High-Level Design

Status: Approved baseline  
Date: 2026-07-29  
Phase: Canonical Education Model

## Context and scope

Phase 3 extends the modular monolith with a tenant-owned, vendor-neutral education
domain and immutable source lineage. It consumes no ERP data yet; Phase 4 connectors
will submit observations through an internal application service.

Included:

- academic periods, programmes and versions;
- courses and versions;
- offerings and teaching assignments;
- minimised learners and enrolments;
- registered source systems, immutable observations, lineage, and reconciliation;
- retention/processing-restriction metadata;
- authorized, versioned management/read APIs.

Excluded:

- connector protocols and ingestion scheduling;
- raw landing payloads and quarantine;
- attendance, assessment, grades, finance, admissions decisions, health, discipline,
  demographics, guardians, free-form notes, risk scores, AI, and write-back;
- student/parent API access;
- automated physical deletion.

## Component view

```text
Authorized API client
        |
        v
Phase 2 OIDC + tenant-context + deny-by-default authorization
        |
        v
Phase 3 canonical API schemas
        |
        v
Canonical application services
   |          |             |
   |          |             +--> Subject-rights service
   |          +--> Reconciliation service
   +--> Academic structure / learner / enrolment services
        |
        v
Tenant-required repositories + audit service
        |
        v
PostgreSQL composite constraints + forced RLS
        |
        +--> canonical records
        +--> immutable source observations and lineage
```

Phase 4 connectors will call an internal observation port, not repositories. The port
accepts normalized, allowlisted observations and delegates authority/conflict logic
to Phase 3 services.

## Domain boundaries

- `academics`: periods, programmes, courses, offerings, teaching assignments.
- `learners`: minimised learner aggregate and processing restriction.
- `enrolments`: effective-dated learner-to-programme/offering relationships.
- `lineage`: sources, immutable observations, canonical links, supersession.
- `reconciliation`: explicit conflicts and human resolution.
- `privacy`: protected identifier access, subject requests, export manifests, and
  deletion eligibility.

The domains share tenant IDs but communicate through typed service interfaces. No
domain may create a cross-tenant relationship.

## Trust boundaries

1. API input, source keys, and future connector observations are untrusted.
2. Phase 2 identity and tenant context are prerequisites, not caller-supplied data.
3. Education-record permission and organizational scope are checked in services.
4. Repositories require tenant context and do not accept an optional tenant.
5. PostgreSQL forced RLS and composite keys independently enforce tenant isolation.
6. Lineage and unmasked identifiers are a stricter sub-boundary.
7. ERP values are evidence, not executable instructions or authorization facts.

## Primary flows

### Canonical structure mutation

1. Authenticate and resolve active tenant context.
2. Require structure permission and matching scope.
3. Validate allowlisted schema and `If-Match` where applicable.
4. Apply transaction-local tenant context.
5. enforce domain and database constraints.
6. persist mutation and minimised audit event atomically.
7. persist idempotent response.

### Source observation reconciliation

1. Future connector supplies registered source identity and normalized observation.
2. Service validates source authority for entity type and mapping version.
3. Store immutable observation without raw payload.
4. Match tenant-local canonical record using approved stable keys.
5. Equivalent value adds lineage only.
6. Deterministic higher-authority value creates a new canonical version.
7. Ambiguous/conflicting value opens a reconciliation issue.

### Protected identifier/subject rights

1. Require dedicated permission, MFA, reason, and bounded query.
2. Audit access before returning unmasked data or export manifest.
3. Apply processing restriction immediately when approved.
4. Record correction/deletion request and disposition without deleting lineage.

## Failure behavior

- absent tenant context: fail closed;
- foreign-tenant identifier: `404 resource_not_found`;
- insufficient scope: `404` when existence is sensitive, otherwise `403`;
- malformed/unknown fields: `422 validation_error`;
- source conflict: `409 reconciliation_required`;
- stale ETag: `412 precondition_failed`;
- conflicting idempotency reuse: `409 idempotency_conflict`;
- prohibited attribute: `422 prohibited_attribute`;
- processing-restricted record: deny ordinary processing with `423
  processing_restricted`;
- audit failure aborts sensitive operations.

## Deployment and operations

- Existing non-owner `NOSUPERUSER NOBYPASSRLS` runtime role is retained.
- Additive migration `0005` is the first permitted Phase 3 schema revision.
- No object store, queue, or connector infrastructure is introduced.
- Logs and telemetry use canonical IDs only and exclude source/institutional keys.
- Readiness expects revision `0005` only after Phase 3 is implemented.
- Backups inherit database encryption and access controls; deletion from backups is
  governed by the approved operational retention procedure in later phases.

## Exit architecture qualities

- vendor-neutral schema;
- immutable tenant ownership;
- source-to-canonical lineage without raw payload retention;
- deterministic conflict behavior;
- least-privilege access and masking;
- temporal history without silent overwrite;
- reversible migration with populated-upgrade evidence.
