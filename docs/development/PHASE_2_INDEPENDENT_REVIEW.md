# Phase 2 Independent Review

Status: Rework required  
Date: 2026-07-29  
Phase: Identity, Institution, and Multi-Tenancy

## Decision

**Rework required.** Phase 2 must not be accepted and Phase 3 must not begin.

## Critical findings

The initial runtime database credential was the PostgreSQL bootstrap superuser and
therefore bypassed forced RLS. This was independently reproduced, corrected by
separating migration and runtime roles, and covered by a real PostgreSQL assertion
that the runtime role is neither superuser nor `BYPASSRLS`. No unresolved critical
finding is currently known in the implemented subset.

## High-priority findings

- The approved API contract is incomplete: hierarchy, lifecycle, membership
  lifecycle, role revocation, security-policy mutation, support-access, and several
  control-plane endpoints are absent.
- Required idempotency keys, ETags/`If-Match`, cursor pagination, delegation and
  last-owner invariants are incomplete.
- Container build, vulnerability scan, and smoke evidence has not been rerun for the
  Phase 2 image from an authorized Docker session.
- Threat-model negative tests and the complete role/scope matrix are incomplete.

## Validation evidence

- PostgreSQL migration cycle: `0001 -> 0002 -> 0001 -> 0002` passed.
- PostgreSQL RLS tenant switch and pooled-connection fail-closed test passed under
  `education_erp_app` (`NOSUPERUSER`, `NOBYPASSRLS`).
- Complete suite: 48 passed; 90.97% coverage.
- Ruff format/lint: passed.
- Strict mypy: passed.
- Bandit: zero findings.
- pip-audit: no known vulnerabilities; unpublished local package skipped.
- Docker: blocked for this execution identity by Windows engine-pipe access denial.

## Required fixes before acceptance

Complete the remaining approved work packages and tests, run all gates including
image scan and container smoke from an authorized Docker session, update OpenAPI and
governance evidence, and repeat this independent review.

## Remediation retest

The expanded implementation passes 50 tests with PostgreSQL at 90.15% coverage,
including lifecycle, hierarchy, tenant suspension, last-owner, ETag, security-policy,
support-access, and RLS cases. Migration `0003 -> base -> 0003`, Ruff, mypy, Bandit,
and pip-audit pass.

Decision remains **Rework required** because persistent idempotent replay, opaque
cursor behavior, complete scoped delegation/contract tests, and the Docker image
gates remain incomplete or externally blocked.

## Final remediation review — 2026-07-29

Decision: **Accepted with minor operational follow-up.**

Persistent mutation replay, opaque cursors, the remaining approved routes,
hierarchy-bound delegation and expanded negative authentication, MFA, permission,
tenant, scope, escalation, precondition, cursor and replay tests close the findings.

Final evidence: 54 PostgreSQL tests with no skips at 90.06% coverage;
`base -> 0003 -> base -> 0003` migration success; Ruff, strict mypy, Bandit,
pip-audit, dependency, SBOM and secret gates passed; final image built; Trivy exited
0 with 0 critical vulnerabilities; API/database are healthy; migration exited 0;
and live/ready smoke passed.

No critical security, isolation, correctness, migration or data-loss finding remains.
Remote protected-branch CI evidence remains a minor operational follow-up. Phase 3
was not started.

## Semantic contract audit addendum — 2026-07-29

The acceptance review additionally verified mutation-header OpenAPI completeness,
role-revocation optimistic concurrency, and explicit active tenant-owner approval for
deletion requests. Additive revision `0004` preserves the deployability of databases
already stamped at `0003`.

Superseding evidence: 55 PostgreSQL tests, no skips, 90.16% coverage; existing
`0003 -> 0004` and full `0004 -> base -> 0004` migrations passed; final image,
Trivy (0 critical, exit 0), healthy Compose services, migration exit 0, smoke,
pip-audit and secret scan all passed. Decision remains **Accepted with minor
operational follow-up**. Phase 3 was not started.

## PostgreSQL API-runtime parity addendum — 2026-07-29

Review now includes protected API execution under `education_erp_app`, not only
SQLite API tests plus raw RLS tests. Platform lifecycle routes establish tenant
context before tenant-table access. Onboarding, activation, suspension,
reactivation and owner-approved deletion request pass with the
`NOSUPERUSER NOBYPASSRLS` credential.

Final evidence is 56 PostgreSQL tests, no skips, 90.32% coverage; a validated
91-component SBOM; and passing final image, Trivy, secret, Compose, migration and
smoke gates. Acceptance remains unchanged. Phase 3 was not started.

## Persistent replay process-boundary addendum — 2026-07-29

The reviewer additionally accepts database-backed replay across application
instance recreation. The PostgreSQL test records a mutation in one instance,
replays it from a new instance, compares the persisted status/body, and verifies
that only one business row exists. This closes the distinction between same-process
repeat handling and durable replay.

All Phase 2 gates were rerun successfully: 56 PostgreSQL tests with no skips and
90.32% coverage; static, dependency and security checks; both migration lifecycles;
91-component SBOM; rebuilt healthy containers; migration exit 0; live/ready smoke;
Trivy 0 critical with exit code 0; and no Gitleaks findings. Decision remains
**Accepted with minor operational follow-up**. Phase 3 was not started.
