# Authoritative Phase 3 — Core Intervention Workflow HLD

Status: Independently accepted design; implementation not approved  
Date: 2026-08-05  
Data policy: generated or irreversibly anonymised examples only

## Objective and boundaries

Deliver a tenant-isolated, human-owned System of Action for educational interventions. Core owns cases, tasks, assignments, deadlines, evidence references, code-only annotations, outcomes and audit. ERP/canonical data remains factual authority. Phase 3 does not add risk scoring, model serving, RAG, AI recommendations, real ERP transport, student/parent access, ERP write-back, email/SMS delivery or free-form case notes.

Core must start, remain ready and complete every workflow when AI is disabled or unavailable. Any future AI contribution is optional, labelled evidence submitted through an authorized Core API, requires human acceptance, and never writes Core tables directly.

## First-release users and scope

- `tenant_owner`: tenant-wide policy and case oversight.
- `registrar`: tenant-wide case creation, triage and outcome administration.
- `department_admin`: assigned-department cases and tasks.
- `case_worker`: explicitly assigned case/task scope only.
- `auditor`: masked read-only workflow and audit views.
- `security_admin`: security metadata only, no case content.
- `platform_admin`: no implicit tenant access.

Dean, teacher, principal and owner scenarios are represented through tenant roles and explicit organizational grants; job title alone grants nothing. Student and parent actors are excluded from first release.

## Components

```text
Authenticated client
  -> Intervention API
     -> Authorization / scope / restriction policy
     -> Case command service -> PostgreSQL (forced RLS)
     -> Task and SLA service -> PostgreSQL
     -> Evidence/annotation service -> PostgreSQL
     -> Outcome service -> PostgreSQL
     -> Read-model service -> PostgreSQL projections
     -> Audit service (atomic)
     -> Transactional outbox -> notification request consumer (delivery deferred)

Canonical service -> read-only authorized learner/enrolment projections
AI boundary -> absent in Phase 3; future optional API client only
```

## Core invariants

1. Every record carries `tenant_id`; relationships use composite tenant foreign keys and forced RLS.
2. A case has exactly one accountable human owner while active; queues are routing aids, not ownership.
3. State transitions use a closed transition table and compare-and-swap version.
4. Every mutation is persistently idempotent and atomically writes audit plus any outbox event.
5. Case scope cannot exceed the actor's current tenant and organizational grants.
6. Canonical facts are referenced by stable IDs/version evidence and never copied as uncontrolled text.
7. Case annotations and evidence are closed codes/references only; free text, prohibited attributes and raw ERP payloads are rejected.
8. SLA deadlines are computed from immutable policy-version snapshots; clock changes never rewrite history.
9. Escalation never expands data access and never silently reassigns accountable ownership.
10. Outcome closure requires a human actor, disposition, evidence sufficiency and open-task policy evaluation.
11. Reporting uses tenant-scoped projections with suppression rules; no direct analytics bypass.
12. Processing restriction blocks ordinary creation/export/notification and permits only approved rights/compliance handling.

## Case lifecycle

`draft -> open -> in_progress -> awaiting_evidence -> in_progress -> resolved -> closed`

Additional transitions: `open|in_progress|awaiting_evidence -> cancelled`; `resolved -> in_progress` by authorized reopen; `draft -> cancelled`. No transition starts from `closed` or `cancelled`. Transition reasons are closed codes; no free-text rationale is accepted.

## Reliability and operations

- API transactions own case/task/evidence/audit/outbox atomicity.
- Scheduler claims due SLA rows with `FOR UPDATE SKIP LOCKED`; escalation records are unique by case, policy step and due instant.
- Consumers use `processed_events`; retries are bounded and dead-lettered without changing Core state.
- Notification delivery is outside Phase 3. Phase 3 produces safe `notification.requested` events only.
- Read models rebuild from authoritative Core rows/outbox sequence and are never mutation authority.

## Privacy and subject rights

Cases use canonical IDs and masked display references. No names, contact details, health, disability, discipline, ethnicity, religion, biometrics, government IDs, guardian data, raw grades/attendance, free text, or arbitrary attributes are accepted. Evidence and annotations are closed codes plus approved canonical references; binary upload and external URLs are excluded. Processing restriction immediately hides ordinary reads and pauses workers/notifications. Corrections append superseding structured rows. Existing subject-rights completion and export-manifest flows must include intervention eligibility/disposition and minimised metadata. Deletion disposition respects legal holds and never physically deletes preserved records in Phase 3. Export is single-subject bounded, MFA plus closed `reason_code` protected, audited and `no-store`.

## Exit gate

Implementation may be accepted only after migration lifecycle, unit/PostgreSQL/API/security/E2E suites, the complete C3-T01–C3-T40 matrix, Core-only/AI-outage tests, tenant isolation, quality/image/SBOM/Trivy/Gitleaks/smoke gates and independent review pass. Phase 4 remains separate.
