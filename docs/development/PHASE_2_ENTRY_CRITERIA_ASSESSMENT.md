# Phase 2 Entry-Criteria Assessment

## Phase

Phase 2 — Identity, Institution, and Multi-Tenancy

Assessment date: 2026-07-29

Initial decision: **Entry blocked**

## Objectives

- Implement institution onboarding and tenant configuration.
- Establish user identity and authentication.
- Enforce server-side roles and permissions.
- Enforce tenant ownership and cross-tenant isolation.
- Audit sensitive identity, institution, and administrative actions.

## Requirements in scope

| Requirement | Scope |
|---|---|
| TEN-001 | Every Phase 2 business record has tenant ownership |
| TEN-002 | Cross-tenant access is denied server-side |
| IAM-001 | Roles and permissions constrain protected APIs |
| AUD-001 | Sensitive access and mutations produce audit records |
| API-001 | Identity and institution APIs remain versioned and use standard errors |
| API-002 | Collection APIs use pagination and correlation IDs |
| SEC-002 | Phase 2 identity, least-privilege, privacy, and persistence controls |
| TST-001 | Unit, integration, API, security, tenant-isolation, and E2E tests |
| DOC-001 | Current API, decision, risk, status, and traceability documentation |

## Sources reviewed

- Original supplied platform mandate
- Master development plan and all development governance documents
- Phase 1 implementation and independent acceptance records
- API documentation and API implementation status
- Security checklist and test strategy
- Current Python source, tests, migrations, Docker, Compose, and CI configuration

No PRD, HLD, LLD, system architecture, system design, identity design, database
design, privacy impact assessment, threat model, or Phase 2 implementation plan was
found.

## Entry-criteria disposition

| Criterion | Result | Blocking reason |
|---|---|---|
| Phase 1 accepted | Met | Locally accepted with remote-CI evidence as minor follow-up |
| Legal tenant boundary and hierarchy approved | **Unmet** | Institution, group, campus, and department boundaries are unresolved |
| Tenant lifecycle approved | **Unmet** | Creation, suspension, deletion, merger, and hierarchy rules are unspecified |
| Identity provider and protocol approved | **Unmet** | Local identity versus OIDC/SAML/federation is unresolved |
| MFA and privileged-access policy approved | **Unmet** | Cannot define secure authentication assurance |
| Role and permission model approved | **Unmet** | Supplied roles are possibilities, not an authorised permission matrix |
| User-to-tenant membership rules approved | **Unmet** | Multi-institution users and platform administration are undefined |
| Privacy/compliance baseline approved | **Unmet** | Jurisdiction, child/student data duties, residency, retention, and deletion are unknown |
| Threat model and impersonation/support policy approved | **Unmet** | High-risk administrative paths cannot be designed safely |
| Deployment trust boundaries approved | **Unmet** | IdP, proxy, TLS termination, token issuer/audience, and secret manager are unknown |

## Why implementation cannot safely begin

These are not minor configurable details. They determine database keys and
constraints, token validation, authorization semantics, audit content, tenant
isolation, administrative privileges, and privacy obligations. Guessing them could
create cross-tenant disclosure, privilege escalation, an incompatible identity
architecture, or unlawful data handling. The original mandate explicitly requires
work to stop under those conditions.

No Phase 2 schema, endpoint, authentication mechanism, role, or placeholder security
logic is introduced by this assessment.

## Required approvals

The product, security, privacy, and platform owners must supply or approve:

1. Tenant definition and hierarchy, including whether tenant means institution,
   institution group, campus, or another legal/data boundary.
2. Whether users may belong to multiple tenants and how tenant context is selected.
3. Identity provider, protocol, issuer/audience, token/session lifetime, account
   linking, provisioning, recovery, and deprovisioning.
4. MFA requirements and privileged/platform-support access policy.
5. A role-permission matrix for institution, campus, department, user, role,
   membership, configuration, and audit operations.
6. Platform-administrator and support-impersonation boundaries, approvals, and audit.
7. Data classification, jurisdiction, residency, retention/deletion, and child-data
   requirements for identity and audit data.
8. Threat model and approved tenant-isolation defence: application enforcement,
   PostgreSQL row-level security, or both.
9. Expected onboarding workflow and who may create, activate, suspend, and delete an
   institution.
10. Approved secrets, key, and token-verification strategy for each environment.

## Conditional implementation task list

After the approvals above are documented:

1. Create the Phase 2 HLD, LLD, threat model, permission matrix, API contract, data
   model, and implementation plan.
2. Record ADRs for tenant hierarchy, identity integration, token/session validation,
   authorization policy, audit model, and database isolation.
3. Add typed identity/tenant configuration that fails closed outside tests.
4. Define institution, campus, department, user identity, membership, role,
   permission, role assignment, tenant configuration, and immutable audit models.
5. Add migrations with tenant foreign keys, uniqueness constraints, lifecycle
   constraints, indexes, and approved row-level-security policies.
6. Implement a request identity and tenant context that cannot be caller-forged.
7. Implement deny-by-default permission checks in application services and
   repositories.
8. Implement institution onboarding and approved identity/membership administration
   APIs with pagination, idempotency, validation, and standard errors.
9. Implement append-only security audit events with minimised, non-secret content.
10. Add unit tests for permission and tenant-context rules.
11. Add PostgreSQL integration tests with at least two tenants and adversarial IDs.
12. Add authentication, authorization, horizontal/vertical escalation, missing-
    context, disabled-user, disabled-tenant, and cross-tenant API tests.
13. Add end-to-end onboarding and role-assignment journeys.
14. Add migration lifecycle, concurrency, uniqueness, idempotency, and audit tests.
15. Run Ruff, strict mypy, Bandit, pip-audit, full pytest/coverage, PostgreSQL
    migration cycle, image scan, secret scan, and container smoke gates.
16. Update OpenAPI, API documentation, traceability, status, decisions, risks,
    security checklist, and independent acceptance evidence.

## Phase decision

Phase 2 is **not started**. Entry is blocked until the required security, product,
privacy, and platform decisions are approved and recorded.

## Reassessment after security-model approval — 2026-07-29

The user explicitly authorized definition and approval of the Phase 2 security model.
The following authoritative project baselines now exist:

- `docs/architecture/PHASE_2_SECURITY_MODEL.md`
- `docs/architecture/PHASE_2_HLD.md`
- `docs/architecture/PHASE_2_LLD.md`
- `docs/architecture/PHASE_2_DATA_MODEL.md`
- `docs/security/PHASE_2_THREAT_MODEL.md`
- `docs/api/PHASE_2_API_CONTRACT.md`
- `docs/development/PHASE_2_IMPLEMENTATION_PLAN.md`

| Criterion | Reassessed result |
|---|---|
| Legal tenant boundary and hierarchy | Met: institution boundary; campus/department are internal scopes |
| Tenant lifecycle | Met: approved state machine and deletion safeguards |
| Identity provider and protocol | Met: external OIDC, authorization code + PKCE clients, JWT bearer API |
| MFA and privileged access | Met: mandatory privileged MFA and recent-auth policy |
| Role and permission model | Met: approved built-in roles, permissions and delegation limits |
| Multi-tenant memberships | Met: explicit membership per institution and one context per request |
| Privacy/child-data baseline | Met for Phase 2: identity/admin minimisation; child users and education data excluded |
| Threat/support model | Met: threat model; no impersonation; expiring approved support access |
| Deployment trust model | Met at design level: exact issuer/audience, JWKS, TLS and secret injection |
| PostgreSQL isolation | Met at design level: composite tenant constraints and forced RLS |

Environment-specific issuer URLs, audiences, regions and secret references remain
deployment configuration, not unresolved architecture choices. They must fail closed
when absent in deployed environments.

Reassessed decision: **Entry criteria met; Phase 2 ready for implementation**.

No application code, API endpoint, or migration was created during this design and
approval activity.
