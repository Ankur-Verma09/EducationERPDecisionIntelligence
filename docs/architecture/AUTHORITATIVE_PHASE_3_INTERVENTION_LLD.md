# Authoritative Phase 3 — Core Intervention Workflow LLD

Status: Independently accepted design; implementation not approved  
Date: 2026-08-05

## Module layout

```text
src/education_erp/interventions/
  contracts.py       closed enums and command/result types
  policy.py          permissions, organization scope, restriction checks
  cases.py           create, assign, transition, reopen and cancel
  tasks.py           task lifecycle and dependency checks
  evidence.py        structured evidence and annotation-code validation
  sla.py             policy snapshots, deadlines, breach/escalation claims
  outcomes.py        resolution and outcome recording
  reporting.py       safe tenant-scoped read projections
  repository.py      tenant-required persistence ports
src/education_erp/api/interventions.py
src/education_erp/persistence/intervention_models.py
```

No module imports AI configuration/client code. A future AI adapter must call public authorized commands as a distinct service principal and cannot import repositories.

## Command pipeline

For every mutation:

1. Authenticate and establish exactly one tenant context.
2. Resolve permission and server-derived organizational scope.
3. Validate closed request schema, learner processing restriction and canonical references.
4. Claim persistent idempotency by actor, tenant, method, concrete route, key and request hash.
5. Lock/version the aggregate where required and evaluate the deterministic transition table.
6. Persist aggregate/history, immutable audit and outbox rows in one transaction.
7. Store the exact safe response for replay after commit.

Cross-tenant, out-of-scope and undisclosable identifiers return the same hidden `404`. Authorization never trusts caller-supplied campus/department scope.

## State machines

### Case

| From | Allowed to | Guard |
|---|---|---|
| draft | open, cancelled | owner assigned before open |
| open | in_progress, awaiting_evidence, cancelled | actor may manage case |
| in_progress | awaiting_evidence, resolved, cancelled | resolution requires outcome draft and task policy |
| awaiting_evidence | in_progress, resolved, cancelled | evidence sufficiency check |
| resolved | closed, in_progress | close window or authorized reopen reason |
| closed | none | terminal |
| cancelled | none | terminal |

### Task

`pending -> in_progress -> completed`; `pending|in_progress -> blocked|cancelled`; `blocked -> pending|cancelled`. Completion requires an accountable assignee and optional structured completion evidence. Case closure cancels only tasks whose policy snapshot permits automatic cancellation; otherwise it fails closed.

## Assignment

- Assignable principals require active tenant membership and compatible organizational scope.
- Case ownership change records `case_assignment_history`; it never deletes the previous owner.
- Self-assignment and reassignment are separately permissioned.
- Delegation cannot exceed the delegator's permission/scope or the case scope.
- Membership suspension immediately removes access; ownership becomes `owner_attention_required` and emits a safe operational event.

## SLA and escalation

- `sla_policy_version` is immutable and selected by tenant, case type and priority.
- Deadlines use UTC instants plus recorded calendar/time-zone version; paused intervals are explicit.
- A scheduler claims due `sla_clock` rows with `SKIP LOCKED` and inserts one `sla_breach` per unique step.
- Escalation creates an alert/assignment proposal and notification event; only an authorized human action changes owner.
- Retry/restart is idempotent. AI availability is not queried.

## Evidence, annotations and outcomes

- Evidence kinds: `canonical_record`, `policy_reference`, `generated_attachment_manifest`, `human_observation`.
- Phase 3 stores no binary and fetches no URL. Attachment manifests are generated-test placeholders only until object-storage design approval.
- Human observation fields are closed: observation code, effective date and confidence band. No rationale or arbitrary JSON.
- Case annotations use closed purpose and observation codes only. Free text and arbitrary rationale are rejected deterministically; annotations cannot alter state.
- Outcomes use closed `outcome_code`, `effective_at`, `follow_up_required`, structured measure references and human attestation.

## Concurrency and temporal rules

- Mutable aggregates expose integer `version` as strong ETag.
- All transitions and assignment changes require `If-Match`; stale writes return `412 precondition_failed`.
- Active owner intervals and active SLA-clock intervals use PostgreSQL exclusion constraints.
- History/outbox/audit/evidence attestations are append-only by trigger and runtime grants.
- Client timestamps never determine ordering; server UTC plus monotonic aggregate version does.

## Case attribute mutation rules

- Case type is immutable after creation. A wrong type is cancelled with a closed reason and a replacement case references it.
- Priority may change only in `open`, `in_progress` or `awaiting_evidence`, by `intervention:manage`, with recent MFA, a closed reason code, idempotency and `If-Match`.
- Priority change appends `case_attribute_history`. It never rewrites the existing SLA snapshot or deadline; an explicit `sla_policy_rebind` command with a separate permission, recent MFA and closed `reason_code` creates a new clock version prospectively.
- SLA rebind is allowed only while the case is `open`, `in_progress` or `awaiting_evidence`, before any breach exists. The new deadline must be strictly later than server `now` and greater than or equal to the current deadline. It cannot shorten, backdate, clear or replace history. Any violation returns `409 sla_rebind_conflict` without mutation/audit-outbox partials.
- Organizational scope may only narrow in place. Widening or moving scope requires cancel-and-recreate so existing readers, tasks and evidence cannot silently become visible to a broader organization.
- Scope narrowing locks the case, validates owner/assignees against the new scope, and fails with `409 scope_conflict` until incompatible assignments are explicitly resolved. Existing history/evidence remains under the case's most restrictive historical access envelope.
- Authorization and active memberships are re-evaluated inside the mutation transaction after the row lock to prevent grant-revocation TOCTOU.

## Reporting projections

Projections include counts by state, priority, age band, SLA status, organization and outcome code. Small-cell suppression defaults to fewer than five; learner-level lists require case read permission and never enter aggregate export. Projection lag and source sequence are exposed. A projection failure cannot block Core commands and cannot create authority.

## Failure semantics

- `409 state_conflict`: invalid deterministic transition.
- `409 ownership_conflict`: assignment invariant failure.
- `409 scope_conflict`: scope mutation conflicts with active ownership/task grants.
- `409 sla_rebind_conflict`: rebind is ineligible, breached, backdated or shortens the current deadline.
- `412 precondition_failed`: missing/stale ETag.
- `423 processing_restricted`: ordinary action blocked.
- `422 prohibited_attribute|invalid_evidence|invalid_cursor`.
- `503 audit_unavailable`: fail closed before sensitive commit.

## Subject-rights integration

- `restrict-processing` takes effect transactionally for ordinary detail/list, task/SLA workers, projections, export and notification requests; compliance-authorized rights processing remains available and audited.
- Correction appends a superseding evidence/annotation/outcome row and links the prior row; attested history is never overwritten.
- Existing subject-rights completion cannot finish until each linked intervention case has a recorded `eligible`, `exempt_legal_hold` or `retained_statutory` disposition.
- Existing subject export manifests include allowlisted case state/history, task state and outcome codes; they exclude annotations, restricted evidence values, audit internals and other learners.
- Deletion requests record disposition and restrict processing. Physical deletion, backup erasure and artifact destruction remain unavailable until separately approved operational policy exists.

## Implementation constraints

Use additive migration `0009` only after explicit implementation approval; never modify `0001`–`0008`. Migration `0009` must be self-contained and use no mutable ORM metadata.
