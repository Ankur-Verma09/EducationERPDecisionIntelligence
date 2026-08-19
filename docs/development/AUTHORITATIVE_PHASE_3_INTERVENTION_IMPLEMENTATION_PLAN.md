# Authoritative Phase 3 — Core Intervention Workflow Implementation Plan

Status: Independently accepted design; implementation prohibited pending explicit approval  
Date: 2026-08-05

## Objectives and requirements

Implement `INT-001` plus Phase 3 portions of `TEN-001`, `TEN-002`, `IAM-001`, `AUD-001`, `API-001`, `API-002`, `SEC-002`, `EVT-001`–`EVT-003`, `OPS-001`, `TST-001` and `DOC-001`. Outcomes are deterministic, human-owned and AI-independent.

## Entry criteria

- Complete HLD, LLD, data model, API/event contract and threat model accepted independently.
- User explicitly approves implementation.
- Revisions `0001`–`0008` hashes preserved.
- Generated-data-only test fixtures approved.
- No critical unresolved design finding.

## Vertical work packages

1. **Contracts and policy**
   - add closed states, actions, reasons, evidence/annotation/outcome types and permission rules;
   - executable transition/property tests and complete C3 traceability skeleton.
2. **Additive persistence `0009`**
   - self-contained tables, composite tenant keys, exclusions, forced RLS, grants and append-only triggers;
   - immutable migration baseline update and both migration lifecycles.
3. **Case creation, ownership and transitions**
   - persistent replay, ETags, atomic audit/outbox and processing-restriction guard;
   - unit, PostgreSQL, API and two-tenant E2E tests.
4. **Tasks and assignments**
   - task lifecycle, assignee scope, ownership history, suspended-owner attention;
   - concurrency, delegation and IDOR negatives.
5. **SLA and escalation**
   - immutable policy snapshots, deadlines, pause/breach claims and proposal-only escalation;
   - time-boundary, retry, crash/restart and competing-worker tests.
6. **Evidence, annotations and outcomes**
   - closed code/reference schemas, deterministic free-text rejection, append-only attestations and resolution guards;
   - privacy, leakage and audit-failure tests.
7. **Reporting and subject rights**
   - rebuildable suppressed projections, lag watermark and metadata-only export manifest;
   - scope, small-cell, restriction, MFA/closed-reason-code and cross-subject negatives.
8. **Events and notification requests**
   - safe versioned event serialization, outbox/consumer dedupe and no-delivery test double;
   - prove consumer cannot mutate Core.
9. **AI independence and operational acceptance**
   - Core-only startup, AI-disabled calls, stop-AI/Core-ready and no-AI-DB-access checks;
   - run quality, dependency, PostgreSQL, migration, SBOM, image, Trivy, Gitleaks and live/readiness smoke gates.
10. **Governance and independent completion review**
   - bind C3-T01–C3-T40 to executable node IDs;
   - update API docs, status, RTM, decisions, risks and migration evidence;
   - fix all critical/high findings before acceptance.

## Test plan

- Unit: state machines, policy/scope, SLA calendar, validation, reporting suppression.
- PostgreSQL: RLS, tenant FKs, exclusion/append-only constraints, races, runtime grants.
- API: OpenAPI headers/schemas/errors/cursors/replay/ETags/MFA/closed reason codes.
- Security: every C3-T01–C3-T40 with positive and negative controls.
- E2E: create-to-close human journey, reassignment, breach/escalation, subject restriction/export, restart/replay, two tenants, Core without AI.

No skip is allowed for PostgreSQL/security acceptance. Coverage must remain at least 90%, with risk-based branch assertions rather than coverage-only acceptance.

## Stop conditions

Stop and return to design review if implementation requires arbitrary evidence JSON, production PII, a new actor class, AI authority, outbound delivery, binary storage, ERP write-back, physical deletion, new case states, weaker RLS/audit, or modification of `0001`–`0008`.

## Definition of done

All planned behavior exists; all applicable tests and gates pass; tenant isolation, human ownership, privacy and AI independence are demonstrated; docs and OpenAPI are current; no unresolved critical/high security finding remains; independent review accepts completion. Phase 4 is not started.
