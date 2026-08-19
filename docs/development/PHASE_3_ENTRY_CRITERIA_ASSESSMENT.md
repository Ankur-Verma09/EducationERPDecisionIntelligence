# Phase 3 Entry-Criteria Assessment

Date: 2026-07-29  
Phase: Phase 3 — Canonical Education Model  
Decision: **Entry criteria met; approved for implementation; implementation not started**

## Objective

Define and implement a tenant-owned canonical education model that preserves ERP
authority and source lineage, enforces relational and lifecycle constraints, and can
support replaceable connectors in Phase 4 without embedding vendor-specific schemas.

Phase 3 does not include ERP connectors, ingestion jobs, validation/quarantine,
scoring, AI, interventions, dashboards, notifications, or write-back.

## Governing sources reviewed

- `MASTER_DEVELOPMENT_PLAN.md`
- `DEVELOPMENT_STATUS.md`
- `REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `ASSUMPTIONS_AND_DECISIONS.md`
- `RISKS_AND_DEPENDENCIES.md`
- Phase 2 HLD, LLD, security model, data model, implementation plan, and threat model
- existing persistence models, tenant context, authorization policies, APIs,
  migrations, and unit/API/integration/security/end-to-end tests

No Phase 3 HLD, LLD, system design, data model, API contract, threat model, privacy
impact assessment, or implementation plan exists. The Phase 2 architecture is the
latest approved architecture and explicitly prohibits student and education-domain
records.

## Requirements in scope

| Requirement | Phase 3 interpretation | Entry status |
|---|---|---|
| SYS-001 | ERP remains authoritative; canonical records cannot silently become the source of truth | Blocked |
| TEN-001 | Every canonical record has immutable institution ownership | Design required |
| TEN-002 | Education-data reads and mutations fail closed across tenants and scopes | Design required |
| AUD-001 | Sensitive education-data access and mutation are auditable and minimised | Design required |
| API-001 | Any Phase 3 API is versioned and uses standard validation/errors | Contract required |
| API-002 | Collections use bounded opaque pagination and request correlation | Contract required |
| DAT-001 | Canonical education model preserves source identifiers and lineage | Blocked |
| DAT-002 | Sensitive/student data is minimised and purpose-limited | Blocked |
| SEC-002 | Least privilege, masking, retention, and deletion apply to the new data | Blocked |
| TST-001 | Appropriate unit, integration, API, security, and end-to-end tests pass | Planned |
| DOC-001 | Architecture, contracts, decisions, risks, and traceability remain current | In progress |

## Initial entry-criteria verification

| Criterion | Result | Evidence or missing input |
|---|---|---|
| Phase 2 locally accepted | Met | Final Phase 2 review and executable gates pass |
| Canonical entity and aggregate scope approved | Unmet | No approved definitions for people/students, academic periods, programmes, courses, sections, enrolments, or organisational relationships |
| Stable identifier and source-lineage semantics approved | Unmet | No rules for source-system identity, natural keys, merges, supersession, temporal history, or conflict precedence |
| ERP authority and mutation policy approved | Unmet | `SYS-001` is mandate-level only; canonical correction and reconciliation behavior is unspecified |
| Student/child data classification and lawful-purpose baseline approved | Unmet | Jurisdiction, age/child status, consent/lawful basis, prohibited attributes, and purpose limitation are unknown |
| Retention, deletion, masking, and subject-rights rules approved | Unmet | R-003 and R-013 remain unresolved |
| Education-data permission and scope matrix approved | Unmet | Phase 2 roles cover administration only; record-level access by registrar, faculty, mentors, students, or parents is undefined |
| Phase 3 threat model approved | Unmet | No abuse cases for bulk access, enumeration, inference, relationship traversal, or lineage leakage |
| Representative anonymised ERP schemas and samples available | Unmet | Critical dependency remains absent |
| Phase 3 HLD, LLD, data model, API contract, and implementation plan approved | Unmet | No Phase 3 design artifacts exist |
| Test and migration strategy approved | Partial | Global strategy exists; Phase 3 fixtures, invariants, populated-upgrade, and deletion tests are undefined |

## Initial blocker rationale

Choosing canonical tables now would decide legal data boundaries, child-data storage,
academic semantics, access scopes, identity merge behavior, retention, and ERP
conflict precedence without authority. Those choices are difficult to reverse after
data is loaded and can create cross-tenant disclosure, unlawful over-collection, or
loss of lineage. The instruction to execute the next *approved* phase does not
approve these missing product, privacy, security, and data-governance decisions.

## Detailed conditional implementation task list

The following work may begin only after the missing entry inputs are approved.

### Work package 1 — Architecture and governance

1. Approve institution types, academic concepts, terminology, and Phase 3 exclusions.
2. Approve data classification, lawful purpose, prohibited attributes, retention,
   masking, deletion, and non-production test-data policy.
3. Approve ERP authority, source-priority, merge, supersession, correction, and
   temporal-history rules.
4. Approve education-data roles, scopes, bulk-access controls, and audit requirements.
5. Produce and approve the Phase 3 HLD, LLD, data model, threat model, API contract,
   and implementation plan.

### Work package 2 — Canonical domain

1. Implement typed domain identifiers and constrained value objects.
2. Implement only the approved canonical aggregates and lifecycle rules.
3. Separate canonical meaning from ERP/vendor field names.
4. Represent effective dates and status history without silently overwriting facts.
5. Add unit tests for every invariant, transition, identifier, and temporal boundary.

### Work package 3 — Lineage and authority

1. Persist source system, source entity type, source record identifier, mapping
   version, observed time, effective time, and canonical-record association.
2. Enforce tenant-consistent source/canonical relationships and uniqueness.
3. Preserve superseded lineage and prohibit unaudited destructive replacement.
4. Implement deterministic conflict/precedence behavior from the approved policy.
5. Add duplicate, replay, merge, split, late-arrival, and conflicting-source tests.

### Work package 4 — Persistence and migrations

1. Add tenant-owned SQLAlchemy models with composite tenant foreign keys.
2. Add additive revision `0005` without modifying revisions `0001`–`0004`.
3. Add check, unique, temporal, and relationship constraints.
4. Enable and force RLS on every tenant-owned Phase 3 table.
5. Grant the runtime role only required CRUD privileges.
6. Test fresh upgrade, `0004 -> 0005`, populated upgrade, downgrade/upgrade, invalid
   relationships, and RLS under `NOSUPERUSER NOBYPASSRLS`.

### Work package 5 — Services and APIs

1. Add repositories and services that require verified tenant context.
2. Enforce approved role and campus/department/record scopes server-side.
3. Add versioned schemas and endpoints only where the approved contract requires.
4. Reuse persistent idempotency, ETags, opaque cursors, request IDs, and safe errors.
5. Audit approved sensitive reads, mutations, bulk operations, and lineage access.

### Work package 6 — Verification

1. Add unit tests for domain and privacy rules.
2. Add PostgreSQL integration tests for constraints, lineage, transactions, RLS,
   pool reuse, migration compatibility, and audit atomicity.
3. Add API contract tests for validation, pagination, idempotency, concurrency, and
   minimised responses.
4. Add security tests for IDOR, cross-tenant joins, guessed IDs, scope escape, bulk
   enumeration, inference, over-posting, lineage leakage, and stale authorization.
5. Add an end-to-end canonical-record and lineage journey using generated data.
6. Run Ruff, strict mypy, pytest/coverage, Bandit, dependency audit, secret scan,
   SBOM, migrations, image scan, Compose health, and smoke gates.
7. Complete an independent review before Phase 3 acceptance.

## Initial inputs required to unblock

1. Approved Phase 3 canonical entity glossary and first-release scope.
2. Approved student/child-data privacy and retention baseline.
3. Approved education-data permission/scope matrix.
4. Approved ERP authority, identifiers, lineage, merge, and temporal rules.
5. Representative generated or irreversibly anonymised ERP schemas and examples.
6. Authorization to create and approve the Phase 3 architecture, threat model, API
   contract, data model, and implementation plan from those inputs.

## Approval update — 2026-07-29

The user explicitly authorized definition and approval of a conservative Phase 3
baseline using generated or irreversibly anonymised examples only. The following
approved artifacts resolve the initial entry blockers:

- `PHASE_3_SECURITY_PRIVACY_MODEL.md`
- `PHASE_3_CANONICAL_SCHEMAS.md`
- `PHASE_3_HLD.md`
- `PHASE_3_LLD.md`
- `PHASE_3_DATA_MODEL.md`
- `PHASE_3_THREAT_MODEL.md`
- `PHASE_3_API_CONTRACT.md`
- `PHASE_3_IMPLEMENTATION_PLAN.md`
- `PHASE_3_INDEPENDENT_REVIEW.md`

The canonical glossary/scope, minimisation and prohibited fields, lawful purpose,
masking, conservative retention, subject-rights boundaries, role/scope matrix, ERP
authority, source precedence, lineage, identifiers, merges, supersession, temporal
semantics, generated schemas, threats, APIs, migration strategy, and executable
gates are now approved.

Reassessed decision: **Phase 3 entry criteria met; ready for implementation.**
Approval is design authorization only. No Phase 3 code, API, test, or migration has
started, and Phase 4 remains prohibited.
