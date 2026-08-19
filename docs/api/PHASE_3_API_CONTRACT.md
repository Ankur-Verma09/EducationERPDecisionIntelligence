# Phase 3 API Contract

Status: Approved baseline  
Date: 2026-07-29  
Base path: `/api/v1`

## Contract rules

- OIDC, tenant context, request IDs, standard errors, persistent idempotency, ETags,
  and opaque cursors reuse Phase 2 controls.
- Every mutation requires `Idempotency-Key`.
- PATCH and transition operations require `If-Match`.
- List limit defaults to 50 and is bounded to 1–100.
- Unknown request fields are rejected.
- Cross-tenant or scope-hidden resources return `404 resource_not_found`.
- Learner references are masked unless a dedicated protected endpoint is used.
- No endpoint accepts or returns raw ERP payloads.

## Academic structure endpoints

```text
GET    /tenants/{tenant_id}/academic-periods
POST   /tenants/{tenant_id}/academic-periods
GET    /tenants/{tenant_id}/academic-periods/{period_id}
PATCH  /tenants/{tenant_id}/academic-periods/{period_id}

GET    /tenants/{tenant_id}/programmes
POST   /tenants/{tenant_id}/programmes
GET    /tenants/{tenant_id}/programmes/{programme_id}
PATCH  /tenants/{tenant_id}/programmes/{programme_id}
POST   /tenants/{tenant_id}/programmes/{programme_id}/versions

GET    /tenants/{tenant_id}/courses
POST   /tenants/{tenant_id}/courses
GET    /tenants/{tenant_id}/courses/{course_id}
PATCH  /tenants/{tenant_id}/courses/{course_id}
POST   /tenants/{tenant_id}/courses/{course_id}/versions

GET    /tenants/{tenant_id}/offerings
POST   /tenants/{tenant_id}/offerings
GET    /tenants/{tenant_id}/offerings/{offering_id}
PATCH  /tenants/{tenant_id}/offerings/{offering_id}
```

Permissions: `academic_structure:read` or `academic_structure:manage`, plus
campus/department scope for offerings.

## Learner endpoints

```text
GET    /tenants/{tenant_id}/learners
POST   /tenants/{tenant_id}/learners
GET    /tenants/{tenant_id}/learners/{learner_id}
PATCH  /tenants/{tenant_id}/learners/{learner_id}
POST   /tenants/{tenant_id}/learners/{learner_id}/restrict-processing
POST   /tenants/{tenant_id}/learners/{learner_id}/resume-processing
POST   /tenants/{tenant_id}/learners/{learner_id}/reveal-reference
```

General read responses:

```json
{
  "id": "10000000-0000-4000-8000-000000000001",
  "institution_reference_masked": "********1007",
  "status": "active",
  "processing_restriction": false,
  "version": 1
}
```

`reveal-reference` requires `learner_identifier:read`, MFA, and:

```json
{"reason": "verified subject access request"}
```

This is an audited sensitive read rather than a mutation: it does not use or persist
an idempotency response. The response is `Cache-Control: no-store` and generates an
audit event before protected data is returned.

## Enrolment endpoints

```text
GET    /tenants/{tenant_id}/programme-enrolments
POST   /tenants/{tenant_id}/programme-enrolments
GET    /tenants/{tenant_id}/programme-enrolments/{enrolment_id}
POST   /tenants/{tenant_id}/programme-enrolments/{enrolment_id}/{action}

GET    /tenants/{tenant_id}/offering-enrolments
POST   /tenants/{tenant_id}/offering-enrolments
GET    /tenants/{tenant_id}/offering-enrolments/{enrolment_id}
POST   /tenants/{tenant_id}/offering-enrolments/{enrolment_id}/{action}
```

Approved actions: `activate`, `suspend`, `withdraw`, `complete`, `cancel`. Invalid
transitions return `409 state_conflict`. Permissions are `enrolment:read` and
`enrolment:manage`.

## Lineage and reconciliation endpoints

```text
GET    /tenants/{tenant_id}/canonical-records/{entity_type}/{record_id}/lineage
GET    /tenants/{tenant_id}/reconciliation-issues
GET    /tenants/{tenant_id}/reconciliation-issues/{issue_id}
POST   /tenants/{tenant_id}/reconciliation-issues/{issue_id}/resolve
POST   /tenants/{tenant_id}/reconciliation-issues/{issue_id}/dismiss
```

Lineage requires `lineage:read` and MFA. Resolution requires
`reconciliation:manage`, MFA, `If-Match`, reason, and a closed `resolution_code`.
Responses contain protected source keys only when explicitly requested through a
future separately approved operation; Phase 3 lineage API returns source code,
observation ID/version, mapping version, authority, and timestamps.

No public source-system registration or observation-ingestion endpoint is approved
in Phase 3. Those are Phase 4 contracts.

## Subject-rights endpoints

```text
GET    /tenants/{tenant_id}/subject-rights-requests
POST   /tenants/{tenant_id}/subject-rights-requests
GET    /tenants/{tenant_id}/subject-rights-requests/{request_id}
POST   /tenants/{tenant_id}/subject-rights-requests/{request_id}/complete
POST   /tenants/{tenant_id}/subject-rights-requests/{request_id}/export-manifest
```

All require MFA and reason. `subject_rights:read/manage` controls request access.
`subject_export:create` creates metadata only; no downloadable artifact is generated
until encrypted object storage is approved.

## Request schemas

Requests use explicit fields from the canonical data model. Representative learner
creation:

```json
{
  "institution_reference": "GEN-LRN-1007",
  "platform_user_id": null
}
```

Any field such as `name`, `date_of_birth`, `gender`, `ethnicity`, `health`,
`discipline`, `guardian`, `address`, `email`, `phone`, `notes`, or arbitrary
`attributes` is rejected with `422 prohibited_attribute`.

## Collection envelope

```json
{
  "items": [],
  "next_cursor": "opaque-or-null"
}
```

Cursors bind route, tenant, stable UUID boundary, filters, and a bounded expiry.
Malformed, tampered, foreign-route, or foreign-tenant cursors return
`422 invalid_cursor`.

## Headers

Responses preserve:

- `X-Request-ID`
- security headers from Phase 1
- `ETag` for mutable detail resources
- `Cache-Control: no-store` for protected identifier, lineage, reconciliation, and
  subject-rights responses

## Errors

The standard envelope is retained:

```json
{
  "error": {
    "code": "temporal_conflict",
    "message": "The requested effective interval conflicts with an existing record.",
    "request_id": "uuid"
  }
}
```

Phase 3 codes:

- `prohibited_attribute` (`422`)
- `processing_restricted` (`423`)
- `reconciliation_required` (`409`)
- `source_not_authorized` (`403`, internal port)
- `temporal_conflict` (`409`)
- existing authentication, permission, scope, state, idempotency, precondition,
  cursor, validation, and not-found codes.

## OpenAPI acceptance

Executable contract tests must prove:

- every mutation documents/requires `Idempotency-Key`;
- every versioned mutation documents/requires `If-Match`;
- all schemas forbid extra fields;
- protected operations document MFA/reason behavior and `no-store`;
- no prohibited or raw-payload field appears;
- pagination limits/cursors and standard errors match implementation.
