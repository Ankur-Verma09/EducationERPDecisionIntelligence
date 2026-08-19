# API Implementation Status

The authoritative Google plan controls phase naming. Identity/tenancy and canonical
education APIs contribute to authoritative Phases 1 and 2. The Sprint 4 integration
framework and Sprint 5 generated demo connector APIs are implemented. A real ERP
connector and authoritative Phase 3 intervention APIs are not implemented.

| API area | Target phase | Status | Notes |
|---|---:|---|---|
| Liveness/readiness | 1 | Verified | `GET /api/v1/health/live` and migration-aware `/ready`; see `docs/api/HEALTH_API.md` |
| Identity/tenant administration | 2 | Verified | Approved Phase 2 contract implemented; PostgreSQL/RLS and container gates pass |
| Canonical education resources | 2 | Verified implemented subset | Previously called local Phase 3; credited to authoritative Phase 2 |
| Connector/sync status | 2 | Verified demo implementation | Sprint 4 framework plus checksum-bound Sprint 5 generated demo profile |
| Validation/data quality | 2 | Verified demo implementation | Closed schema, quarantine, reconciliation and threshold controls |
| Risk scoring/explanations | 6 | Planned | Deterministic rules first |
| Knowledge/AI explanation | 7 | Planned | Grounded, authorised retrieval only |
| First real ERP connector/operator APIs | 2 | Blocked for production | Demo profile is not real-source authority; production owners and transport remain absent |
| Interventions | 9 | Missing | Future workflow and approval policy required |
| Dashboard/reporting | 10 | Missing | Future leadership read models required |
| Notifications/write-back | 3+ | Missing | Phase 3 notifications; controlled ERP write-back remains later scope |

Every endpoint must eventually be linked to OpenAPI, authorisation rules, requirement
IDs, implementation files, and positive/negative/tenant-isolation tests.

Phase 1 has no collection or business endpoints, so pagination, authentication,
authorisation, idempotency, and tenant isolation are not applicable to its two
read-only operational endpoints. These requirements are not considered completed
globally.

## Phase 2 entry update — 2026-07-29

Identity, institution, membership, role, permission, tenant-configuration, and audit
APIs remain **blocked at design entry**. No endpoint contract can be approved until
the tenant boundary, identity provider/protocol, permission matrix, lifecycle rules,
privacy constraints, and threat model are approved.

The Phase 2 API contract is now approved in
`docs/api/PHASE_2_API_CONTRACT.md`. Endpoint implementation remains `Planned`; no API
is represented as implemented until authorization, RLS, audit and negative tests
pass.

## Phase 2 completion update — 2026-07-29

All synchronous endpoints in `docs/api/PHASE_2_API_CONTRACT.md` are implemented.
Physical deletion execution remains excluded as approved; the API records an audited
deletion request.

Mutations persist and replay idempotent responses; updates enforce ETags; collections
return `{items, next_cursor}` with bounded opaque cursors. Platform/tenant separation,
hidden lookups, MFA, last-owner, hierarchy-bound delegation, support expiry and
immutable audit controls pass. Final verification: 54 PostgreSQL tests, no skips,
90.06% coverage, migration `0003`, image, Trivy, Compose and smoke gates passed.

### Semantic contract audit

OpenAPI now declares `Idempotency-Key` for every mutation. Role-assignment
revocation exposes and enforces versioned `If-Match`. Institution deletion requests
require an active tenant-owner membership approval. Final verification supersedes
the prior count: 55 PostgreSQL tests, no skips, 90.16% coverage, revision `0004`,
and all image/scan/Compose/smoke gates passed.

### PostgreSQL API-runtime parity

Platform onboarding, activation, suspension, reactivation and owner-approved
deletion request now have a real API integration test under the
non-superuser/non-`BYPASSRLS` PostgreSQL runtime.
Platform lifecycle handlers set transaction-local tenant context before tenant-table
access. Superseding count: 56 PostgreSQL tests, no skips, 90.32% coverage.

## Persistent replay process-boundary addendum — 2026-07-29

The PostgreSQL API integration journey now recreates the FastAPI application and
database session factory before replaying a completed campus mutation. The second
instance returns the persisted response, and a privileged verification query
confirms one and only one campus row. This proves replay is database-backed rather
than process-memory-backed. The approved Phase 2 API remains complete; Phase 3 has
not started.
