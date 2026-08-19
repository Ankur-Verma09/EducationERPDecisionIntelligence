# Phase 3 Independent Design Review

Review date: 2026-07-29  
Review scope: Phase 3 design and entry artifacts only  
Implementation reviewed: none  
Decision: **Approved for implementation with mandatory design constraints**

## Independence statement

This review evaluates the Phase 3 artifact set against the governing mandate,
accepted Phase 2 boundaries, entry assessment, traceability, privacy/security risks,
and test strategy. It does not claim that Phase 3 code, migration, APIs, tests, or
deployment gates exist.

## Artifacts reviewed

- Phase 3 entry assessment
- security and privacy model
- canonical glossary and representative generated schemas
- HLD and LLD
- data model
- threat model
- API contract
- implementation plan
- master plan, decisions, risks, traceability, and Phase 2 architecture

## Findings

### Scope and future-phase control — Pass

The design stays within the canonical model. It excludes connectors, ingestion
transport, quarantine, grades, attendance, finance, risk, AI, interventions,
dashboards, notifications, and write-back. Phase 4 is not started.

### Data minimisation and child-data posture — Pass

The first release treats all learners as potentially children and excludes names,
contact details, birth dates, demographics, guardians, health, discipline, notes,
biometrics, and government identifiers. Learner identity is tenant-local and
generated. Examples are explicitly fictional.

### Lawful purpose, retention, and rights — Pass with deployment prerequisite

Purpose, prohibited uses, masking, processing restriction, subject-rights metadata,
and conservative retention defaults are defined. Jurisdiction-specific lawful basis,
deadlines, legal holds, and backup erasure remain deployment/operational approvals
and are correctly identified as production prerequisites rather than invented.

### Tenant isolation and authorization — Pass

Application policy, organizational scope, composite tenant foreign keys, forced RLS,
hidden lookup behavior, no implicit platform access, and stricter identifier/lineage
permissions form layered controls. Teaching assignments do not grant authority.

### ERP authority and lineage — Pass

The ERP remains authoritative by registered entity type. Observed time and effective
time are distinct; recency alone cannot override authority. Immutable observations,
semantic equivalence, deterministic precedence, explicit reconciliation, and
supersession prevent silent history destruction.

### Relational and temporal integrity — Pass

Stable roots, effective-dated versions, exclusion constraints, composite tenant keys,
and append-only history are appropriate. The approved per-entity lineage link tables
provide database-enforced target existence and tenant consistency without unchecked
polymorphic IDs or triggers.

### API safety — Pass

The contract reuses tested Phase 2 controls, forbids extras/raw payloads, masks
identifiers, bounds lists, requires protected permissions/MFA/reasons, and limits
subject export to metadata. Phase 4 observation ingestion is not exposed early.

### Threat coverage — Pass

The model enumerates tenant, scope, enumeration, over-posting, telemetry leakage,
source authority, temporal, replay, concurrency, restriction, export, audit, and
raw-payload threats. Each is assigned an executable or operational verification.

### Implementability and testability — Pass

The plan is divided into vertical work packages with explicit exit criteria and
unit, PostgreSQL, API, security, E2E, migration, image, scan, and smoke gates.

## Mandatory constraints for implementation

1. Do not add an arbitrary JSON/raw payload column.
2. Do not add a globally shared learner/person identity.
3. Do not expose names, demographics, grades, attendance, finance, health,
   discipline, guardians, or notes.
4. Do not derive authorization from teaching assignments.
5. Do not use unchecked polymorphic lineage targets.
6. Do not alter migrations `0001`–`0004`.
7. Do not expose connector ingestion or physical deletion in Phase 3.
8. Stop for design approval if a required behavior is absent or contradictory.

## Entry decision

The prior entry blockers are resolved at design level by the explicitly authorized
conservative baseline. The Phase 3 artifacts are internally consistent and sufficient
to begin implementation.

Approval means **ready to implement Phase 3**, not complete. Phase 3 remains
unimplemented until all functionality and executable gates pass. Phase 4 must not
begin.

## Implementation completion review — 2026-07-29

Decision: **Rework required.**

Passing evidence:

- 68 PostgreSQL tests, no skips, 90.26% coverage;
- Ruff, strict mypy, Bandit, pip-audit, dependency consistency and SBOM;
- additive revision `0005`, existing-head and full migration lifecycles;
- forced-RLS/runtime-role test;
- rebuilt healthy containers and successful migration/smoke;
- Trivy 0 critical, exit code 0; Gitleaks clean.

Blocking findings:

1. Only learner lineage has a concrete link table; the approved per-entity lineage
   set is incomplete.
2. Source authority rules persist, but the deterministic observation-to-projection,
   precedence, equivalence, late-arrival, and conflict services are incomplete.
3. Approved PostgreSQL temporal exclusion/overlap constraints and enrolment status
   history are incomplete.
4. Append-only protection exists at the SQLAlchemy event layer but is not independently
   enforced by PostgreSQL privileges/triggers for every history table.
5. Reconciliation dismissal and subject-rights completion/export-manifest endpoints
   are missing.
6. The automated threat-model matrix does not yet demonstrate every P3-T01–P3-T26
   executable case.
7. Revision `0005` currently creates tables from application metadata. It must be
   converted to a self-contained immutable Alembic definition so future model edits
   cannot change historical migration behavior.

### Remediation continuation

Finding 5 is closed: reconciliation dismissal and subject-rights completion/export
manifest operations now exist. Database remediation also adds nine concrete lineage
tables, four temporal exclusion constraints, enrolment status history, immutable
history triggers, forced RLS, and restricted runtime grants. Deterministic
source-authority dispositions cover creation, equivalence, precedence, and late
conflict.

Revalidation passes 68 PostgreSQL tests with no skips and 90.26% coverage; fresh,
existing-head downgrade/upgrade, and full base lifecycle migrations; all quality
gates; healthy rebuilt API/database with migration exit 0; live/ready smoke; Trivy
zero critical with exit code 0; and Gitleaks clean.

Findings 1–4 are closed only for database structure and deterministic disposition
rules. They remain open at application acceptance scope because persistence and
retrieval of lineage, and observation-to-projection reconciliation, are not complete
for every approved canonical entity. Findings 6 and 7 remain open: the complete
applicable P3-T01–P3-T26 matrix is not automated, and revision `0005` still imports
mutable application metadata instead of owning an immutable schema definition.
Decision remains **Rework required**.

No critical vulnerability is demonstrated in the implemented subset, but required
functionality and defense-in-depth evidence are missing. Phase 3 must not be marked
complete, and Phase 4 must not begin.

## Independent final-remediation review — 2026-07-30

Decision: **Rework required.**

Closed findings:

- revision `0005` is self-contained, owns explicit table definitions, imports no
  application metadata, and passes downgrade/upgrade and base-to-head lifecycles;
- database and application lineage types now exist for all nine approved entities;
- an internal persistent reconciliation service and generic lineage read contract
  exist;
- 73 PostgreSQL tests pass with no skips at 90.88% coverage, and quality, image,
  Trivy, Gitleaks and smoke gates pass.

Remaining blockers:

1. Threat traceability currently verifies referenced test-node existence, but several
   mappings do not execute the stated negative case, including platform-role access,
   organisational scope escape, telemetry leakage, protected identifiers,
   adversarial source keys, export scope/rate/expiry, retention/no-delete, bound
   cursors, cross-actor replay, audit outage, and operational export retention.
2. Phase 3 cursors are opaque encodings but are not signed or bound to tenant, route,
   filters and expiry as required by P3-T22.
3. Reconciliation uses observation time as late-arrival time and has no separate
   effective business time. It does not reject inactive source systems, and the
   current-authority join does not constrain the rule to its effective interval.
4. Reconciliation persistence is tested with SQLite and learner lineage only; no
   PostgreSQL replay/race or all-entity persistence/projection matrix exists.
5. Sensitive Phase 3 reasons are validated but not persisted in audit records.
   Subject-rights reads do not require a reason, despite the approved contract.
6. Generic lineage reads return an empty success for nonexistent canonical records
   rather than verifying target existence and returning a hidden `404`.

Phase 3 is not accepted. Phase 4 must not begin.

## Final acceptance review — 2026-07-30

Decision: **Accepted.**

Final review verified signed/bound cursors, complete lineage responses, sensitive
audit reasons, subject-rights read reasons, distinct effective-time authority,
all-nine PostgreSQL lineage/projection/audit, concurrent replay, temporal overlap
rejection, and substantive P3-T01–P3-T26 evidence. The independent targeted suite
passed 20 tests. The complete PostgreSQL suite passed 88 tests with no skips at
90.67% coverage. Migration, quality, image, Trivy, Gitleaks and smoke gates pass.
No substantive Phase 3 acceptance blocker remains. This does not authorize Phase 4.
