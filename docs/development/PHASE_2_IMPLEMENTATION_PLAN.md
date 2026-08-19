# Phase 2 Implementation Plan

Status: Approved for implementation after entry reassessment  
Date: 2026-07-29  
Phase: Identity, Institution, and Multi-Tenancy

## Objectives

Implement the approved Phase 2 security model, institution control plane, external
OIDC identity mapping, tenant memberships, built-in RBAC, layered tenant isolation,
and immutable security audit.

## Requirements

TEN-001, TEN-002, IAM-001, AUD-001, API-001, API-002, SEC-002, TST-001 and DOC-001.

## Scope

Included:

- institution, campus, department and security-policy administration;
- external OIDC access-token validation;
- users, external identities and tenant memberships;
- built-in roles, permissions and scoped role assignments;
- tenant context and deny-by-default authorization;
- PostgreSQL composite tenant constraints and forced RLS;
- append-only audit events;
- approved support-access grant workflow;
- documented APIs and complete negative security tests.

Excluded:

- local passwords, password recovery and refresh-token storage;
- SAML and machine-to-machine credentials;
- custom role creation;
- student/parent identities;
- institution groups with inherited access;
- canonical education records and all Phase 3+ features;
- physical tenant-deletion job execution and production infrastructure.

## Implementation sequence

### Work package 1 — Foundation and configuration

1. Add dependencies for standards-compliant JWT/OIDC validation.
2. Add typed issuer, audience, algorithm, JWKS cache, MFA and rate-limit settings.
3. Fail closed in deployed environments.
4. Add configuration and token-validation unit tests.

### Work package 2 — Persistence and migration

1. Add SQLAlchemy metadata and Phase 2 models.
2. Create migration for all approved Phase 2 tables, constraints and indexes.
3. Seed built-in roles and permissions deterministically.
4. Add forced RLS policies and runtime/migration role documentation.
5. Test fresh and populated upgrade/downgrade/upgrade against PostgreSQL.

### Work package 3 — Authentication and tenant context

1. Implement OIDC discovery/JWKS adapter behind an interface.
2. Validate issuer, audience, algorithm, signature and token time/required claims.
3. Resolve external identity to active platform user.
4. Resolve explicit tenant context through active membership.
5. Add malformed/stale/wrong-trust/unknown-key and missing-context tests.

### Work package 4 — Authorization

1. Implement canonical permission constants and built-in role mappings.
2. Implement tenant and platform policies separately.
3. Enforce campus/department scopes, delegation limits and recent MFA.
4. Implement security epochs and revocation behavior.
5. Add role matrix, horizontal/vertical escalation and concurrency tests.

### Work package 5 — Domain services and repositories

1. Implement institution/campus/department lifecycle services.
2. Implement membership invitation, activation, suspension and revocation.
3. Implement role assignment/revocation and last-owner invariant.
4. Implement tenant security policy.
5. Implement idempotency and optimistic concurrency.
6. Ensure repositories require tenant context and execute under forced RLS.

### Work package 6 — Audit and support access

1. Implement append-only audit repository/service.
2. Make sensitive mutation and audit atomic.
3. Implement time-limited support grants without impersonation.
4. Add audit completeness, immutability, expiry and self-extension negative tests.

### Work package 7 — APIs and documentation

1. Implement the approved versioned endpoints.
2. Add explicit request/response schemas, cursor pagination, ETags and idempotency.
3. Preserve Phase 1 errors, correlation IDs and security headers.
4. Generate/test OpenAPI and update Markdown API documentation.

### Work package 8 — Validation

1. Unit tests for domain, permissions, token validation and transitions.
2. PostgreSQL integration tests with two or more tenants.
3. API authentication/authorization/isolation and boundary tests.
4. E2E onboarding, invitation, role assignment, suspension and isolation journey.
5. Security tests from every threat-model abuse case.
6. Ruff, strict mypy, Bandit, pip-audit, coverage, migration cycle, secret scan,
   image build/scan and container smoke.
7. Independent review before acceptance.

## Exit criteria

- Approved OIDC users authenticate; invalid tokens fail closed.
- Every Phase 2 tenant-owned record has immutable tenant ownership.
- Cross-tenant negative tests pass at service, repository and RLS layers.
- Built-in roles restrict access according to the approved permission matrix.
- Missing tenant context and pooled-connection reuse fail closed.
- Privileged operations enforce MFA/recent authentication.
- Sensitive mutations and support access generate immutable, minimised audit events.
- Migrations and rollback pass against PostgreSQL.
- API/OpenAPI documentation matches implementation.
- All relevant tests and security/supply-chain/container gates pass.
- No critical security, tenant-isolation, correctness or data-loss issue remains.

## Rollback

Application deployment can roll back only while the migration compatibility window
is maintained. The Phase 2 downgrade is tested in non-production environments.
Production tenant/audit deletion is not used as an ordinary rollback mechanism.

## Delivery strategy

Implement in small work packages and keep Phase 2 unaccepted until the complete
cross-tenant and authorization matrix passes. Do not begin Phase 3.
