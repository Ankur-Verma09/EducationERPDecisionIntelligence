# Authoritative Phase 3 — Core Intervention Workflow Data Model

Status: Independently accepted design; implementation not approved  
Date: 2026-08-05

## Tenant-owned aggregates

| Table | Purpose | Principal controls |
|---|---|---|
| `intervention_case` | Case identity, type, priority, state, scope, owner, learner reference, version | forced RLS; composite tenant FKs; no free-form payload |
| `case_state_history` | Append-only transitions and reason codes | append-only; actor/audit correlation |
| `case_assignment_history` | Append-only accountable-owner intervals | exclusion constraint on active interval |
| `intervention_task` | Bounded work item, assignee, state, due date, version | forced RLS; case/assignee tenant consistency |
| `task_state_history` | Append-only task transitions | append-only |
| `case_evidence` | Structured evidence metadata/reference | allowlisted kind; no URL/blob/raw ERP payload |
| `case_annotation` | Closed purpose/observation codes only | no free text; append-only supersession |
| `case_attribute_history` | Type/priority/scope changes and closed reasons | append-only; type immutable; scope narrowing only |
| `sla_policy_version` | Immutable tenant policy snapshot | unique tenant/code/version; append-only |
| `case_sla_clock` | Deadline, pause intervals and current step | one active compatible clock per case |
| `sla_breach` | Idempotent breach/escalation record | unique case/policy step/due instant |
| `case_outcome` | Human-attested resolution/outcome | one active final outcome; supersession history |
| `intervention_report_projection` | Rebuildable safe aggregate | non-authoritative; tenant RLS; sequence watermark |

Existing `audit_event`, `idempotency_record`, `outbox_event`, `processed_event`, canonical learner/enrolment and subject-rights tables are reused; no duplicate identity or raw source store is added.

## Required columns and keys

Every table has UUID `id`, `tenant_id`, server timestamps and composite unique `(tenant_id, id)`. Mutable aggregates have positive integer `version`. Case scope stores nullable `campus_id` and `department_id` with tenant-consistent FKs; the most specific non-null scope governs. `learner_id` references the tenant-local canonical learner. Owner/assignee references platform users only through active tenant membership validation.

Case type, priority, state, reason, task type/state, evidence kind, annotation code, outcome code and classification are closed database enums/check constraints. Free text, arbitrary JSON, binary, URL, contact, demographic, health, disability, discipline, finance and guardian columns are prohibited.

## Temporal and append-only semantics

- State and assignment histories use `[effective_from, effective_to)` UTC ranges.
- Exclusion constraints prevent overlapping active ownership and incompatible SLA intervals.
- History, evidence attestations, policy versions, breach, audit and outbox rows reject update/delete for the runtime role.
- Corrections append superseding rows; they do not rewrite attestations.
- Case/task soft retirement is represented by terminal state, never deletion.

## Subject rights, retention and deletion

- A case inherits the learner processing-restriction state at command time.
- Rights export joins by tenant and learner and emits minimised case/task/outcome codes, excluding restricted evidence and annotations.
- Correction adds a superseding structured record and audit link.
- Rights completion requires an intervention disposition per linked case; processing restriction applies to reads, workers, projections, export and notifications.
- Deletion requests produce `eligible`, `exempt_legal_hold` or `retained_statutory` disposition metadata; physical deletion is deferred until jurisdiction, legal-hold, backup and artifact procedures are approved.
- Default design retention is configurable metadata, not a production schedule. No production data is permitted without owner-approved policy.

## Indexing and isolation

Indexes begin with `tenant_id` for case state/scope/owner, task assignee/state/due, SLA due/status and projection dimensions. RLS uses the established transaction-local tenant context. Runtime roles are `NOSUPERUSER NOBYPASSRLS`; migration ownership is separate. Foreign-tenant joins fail through composite keys even if application checks regress.

## Migration acceptance

Future `0009` must create and downgrade only these Phase 3 objects, install forced RLS and append-only enforcement, grant least privilege, and pass `0008 -> 0009 -> 0008 -> 0009` plus `head -> base -> head`. No implementation or migration is authorized by this design.
