# Phase 2 Implemented API

Status: Complete and locally accepted  
Base path: `/api/v1`

The approved contract is `PHASE_2_API_CONTRACT.md`. This document summarizes the
implemented and tested API.

## Authentication and authorization

Protected endpoints require an OIDC JWT bearer access token. The API validates exact
issuer, audience, asymmetric algorithm, signature, expiry, issue time, and required
claims using JWKS. Invalid or missing tokens use the standard error envelope.

Tenant endpoints resolve an active membership, derive permissions from persisted role
assignments, set transaction-local PostgreSQL tenant context, and return tenant-hidden
resources as `404`. Platform administration requires a persisted platform role and
MFA. Scoped delegation is hierarchy-bound and cannot escalate the caller's authority.

## Implemented endpoint groups

- current-principal (`GET /me`)
- platform institution onboarding, activation, suspension, and deletion requests
- tenant details, campuses, and departments
- membership creation, suspension, and revocation
- role assignment and version-checked revocation
- tenant security-policy read and mutation
- support-access grant and revocation
- MFA-protected audit-event access

Institution onboarding atomically creates the institution, initial owner identity,
active membership, tenant security policy, owner role assignment, and audit event.

All mutations use persistent idempotent replay. Versioned resources enforce
`If-Match`; collections use bounded opaque cursors. Physical deletion execution
remains intentionally outside the synchronous Phase 2 API.

## Validation — 2026-07-29

The generated OpenAPI contract documents `Idempotency-Key` on every mutation.
Persistent replay was verified across application-instance recreation against
PostgreSQL through the least-privileged runtime role, with exactly one resulting
business row.

Platform lifecycle routes establish transaction-local tenant context before
RLS-protected tenant-table access. A PostgreSQL API journey verifies onboarding,
activation, suspension, reactivation, and owner-approved deletion requests.

Accepted evidence: 56 PostgreSQL tests passed with no skips at 90.32% coverage;
revision `0004`; both supported migration lifecycles; all quality, dependency,
image, scan, container-health, and smoke gates. Phase 3 has not started.
