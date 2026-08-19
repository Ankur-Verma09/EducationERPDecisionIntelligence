# Phase 3 Implementation Plan

Status: Approved for implementation after entry reassessment  
Date: 2026-07-29  
Phase: Canonical Education Model

## Objectives

Implement the approved vendor-neutral, tenant-owned canonical education model,
minimised learner/enrolment records, immutable source lineage, deterministic
reconciliation, and privacy controls without adding ERP connectors or future-phase
analytics.

## Requirements

SYS-001, TEN-001, TEN-002, AUD-001, API-001, API-002, DAT-001, DAT-002, SEC-002,
TST-001, and DOC-001.

## Approved design sources

- `PHASE_3_SECURITY_PRIVACY_MODEL.md`
- `PHASE_3_CANONICAL_SCHEMAS.md`
- `PHASE_3_HLD.md`
- `PHASE_3_LLD.md`
- `PHASE_3_DATA_MODEL.md`
- `PHASE_3_THREAT_MODEL.md`
- `PHASE_3_API_CONTRACT.md`

If implementation exposes a contradiction or requires a material new field, role,
retention rule, endpoint, or trust boundary, stop and amend/approve the design before
coding it.

## Scope

Included:

- periods, programmes/versions, courses/versions, offerings;
- minimised learners, programme/offering enrolments, status history;
- teaching assignments as non-authorizing data;
- source-system registrations, authority rules, observations, concrete lineage;
- reconciliation issues and approved resolution;
- processing restriction and subject-rights request/export-manifest metadata;
- approved management/read APIs;
- tenant constraints, forced RLS, audit, masking, retention metadata;
- complete automated and deployment validation.

Excluded:

- ERP connector adapters, credentials, file/REST/database ingestion and scheduling;
- raw landing data and quarantine;
- demographics, contacts, guardians, grades, attendance, finance, health, discipline,
  admissions decisions, notes, risk/AI/workflows/dashboards;
- student, parent, and implicit faculty access;
- learner merge/split public APIs;
- downloadable subject exports and automated physical deletion;
- Phase 4 and later work.

## Work package 1 — Shared controls and access definitions

1. Add canonical Phase 3 permissions and conservative built-in role mappings.
2. Add centralized education-scope and processing-restriction policy functions.
3. Add protected-response/no-store and reason validation helpers.
4. Unit-test every role/permission/scope/MFA/restriction branch.

Exit: deny-by-default matrix matches the approved privacy model.

## Work package 2 — Academic domain and migration foundation

1. Implement domain value objects, statuses, intervals, and transitions.
2. Implement academic period, programme/version, course/version, and offering models.
3. Add initial portion of additive migration `0005` with composite tenant keys,
   indexes, temporal checks, forced RLS, and grants.
4. Add PostgreSQL tests for constraints, interval overlap, hierarchy consistency,
   runtime role, RLS, and pool reuse.

Exit: academic structure persists safely under the runtime role.

## Work package 3 — Learner and enrolment domain

1. Implement minimised learner storage with protected reference/fingerprint boundary.
2. Implement programme/offering enrolments and append-only status history.
3. Enforce processing restriction and retention metadata.
4. Extend `0005` and integration tests for tenant, temporal, uniqueness, concurrency,
   and append-only invariants.

Exit: no prohibited field exists in models/migration; cross-tenant relationships fail.

## Work package 4 — Lineage and reconciliation

1. Implement source system and authority-rule models.
2. Implement immutable allowlisted observation model with no raw payload.
3. Implement the approved concrete per-entity lineage link tables with composite
   observation and canonical-target tenant foreign keys.
4. Implement deterministic matching, authority, equivalence, late-arrival, and
   conflict behavior.
5. Implement reconciliation issue and resolution state machine.
6. Add replay, race, precedence, conflict, supersession, immutability, and audit
   tests.

Exit: every projection is traceable and conflicts never silently overwrite.

## Work package 5 — Privacy and subject rights

1. Implement masked learner responses and protected reference reveal.
2. Implement processing restriction/resumption.
3. Implement subject-rights request and export-manifest metadata.
4. Implement retention/deletion eligibility without physical deletion.
5. Add audit-failure, unmask, reason, MFA, restriction, export-scope, and
   minimisation tests.

Exit: sensitive paths fail closed and emit minimised audit events.

## Work package 6 — Repositories and services

1. Add tenant-context-required repositories by domain.
2. Add services with explicit authorization and transaction boundaries.
3. Reuse persistent idempotency and optimistic concurrency.
4. Make canonical mutation, lineage/reconciliation change, and audit atomic.
5. Add service/component tests including missing context and stale authorization.

Exit: handlers do not query SQLAlchemy directly; services enforce all rules.

## Work package 7 — APIs and contract

1. Implement approved Phase 3 routes only.
2. Add explicit Pydantic schemas with forbidden extras and bounded values.
3. Add ETags, idempotency headers, opaque bound cursors, no-store, and standard
   errors.
4. Add OpenAPI tests for every route/header/schema/security behavior.
5. Add positive/negative API tests for role, scope, tenant, state, concurrency,
   prohibited fields, masking, and restriction.

Exit: generated OpenAPI matches the approved Markdown contract.

## Work package 8 — End-to-end and security validation

1. Add generated two-tenant E2E journey: structure, learner, enrolment, lineage,
   correction/reconciliation, restriction, and isolation.
2. Automate every Phase 3 threat-model test or document the operational gate.
3. Test PostgreSQL populated `0004 -> 0005`, `0005 -> 0004 -> 0005`, and full
   lifecycle.
4. Run Ruff, strict mypy, full PostgreSQL pytest/coverage, Bandit, pip-audit,
   `pip check`, SBOM validation, Gitleaks, image build, Trivy, Compose migration,
   health, and smoke tests.
5. Update API/status/traceability/decisions/risks and perform independent review.

Exit: no unresolved critical security, privacy, tenant-isolation, lineage,
correctness, migration, or data-loss finding.

## Test requirements

- Unit: value objects, intervals, transitions, role matrix, masking, precedence,
  restriction, retention, subject-rights rules.
- Integration: every constraint, forced RLS table, cross-tenant join, pool reuse,
  append-only behavior, atomic audit, conflicts, races, and migration path.
- API: all approved endpoints, schemas, errors, headers, pagination, idempotency,
  ETags, minimisation, MFA/reason.
- Security: all P3-T01 through P3-T26 applicable executable cases.
- E2E: generated data only; at least two tenants and two organizational scopes.

Coverage must remain at least 90% branch-aware globally, with explicit branch tests
for authorization, temporal, lineage, reconciliation, restriction, and masking logic.

## Migration strategy

- only additive revision `0005`;
- never edit `0001`–`0004`;
- one reviewed migration may be split into `0005` sub-revisions only if deployment
  compatibility requires it;
- populated upgrade must preserve all Phase 2 rows;
- downgrade is destructive to Phase 3 data and is test-only after explicit backup;
- application deployment must maintain a documented compatibility window.

## Definition of done

Phase 3 is complete only when:

- all approved functionality exists;
- every Phase 3 table has immutable tenant ownership and forced RLS;
- lineage is complete, constrained, immutable, and free of raw payloads;
- privacy/minimisation/masking/restriction controls pass;
- role/scope/tenant negatives pass;
- all migration, quality, security, image, and smoke gates pass;
- API and governance documents match implementation;
- independent review accepts the phase.

Do not begin Phase 4 before Phase 3 acceptance.
