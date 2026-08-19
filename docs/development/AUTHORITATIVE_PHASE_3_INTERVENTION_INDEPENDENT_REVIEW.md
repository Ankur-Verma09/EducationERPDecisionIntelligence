# Authoritative Phase 3 — Core Intervention Workflow Independent Design Review

Date: 2026-08-05  
Disposition: **Accepted for design; implementation not approved**

## Scope reviewed

The reviewer assessed the intervention HLD, LLD, data model, API/event contract, threat model, implementation plan, entry assessment and controlling governance as principal architect, security reviewer and SDET. Review covered human ownership, deterministic states, assignment/tasks, SLA/escalation, evidence/annotations, outcomes/reporting, authorization, replay/concurrency/audit, notification events, privacy/subject rights, AI independence, generated-only scope and phase boundaries.

## Findings and remediation

Initial review required removal of free-text comments/rationale, closed case-attribute mutation semantics, full subject-rights participation, expanded negative-security coverage and authoritative RTM alignment. Remediation removed all first-release free text, made type immutable and scope narrowing-only, added transactional authorization re-evaluation, priority history and prospective SLA rebind, bound restriction/correction/completion/export/deletion disposition, and expanded C3-T01–C3-T40.

Second review required consistent annotation/reason terminology and executable SLA-rebind rules. Remediation made every reason a closed `reason_code`; rebind is allowed only for active eligible states before breach, with deadline strictly after server time and not earlier than the current deadline, otherwise atomic `409 sla_rebind_conflict`.

Final review found the design technically acceptable and required correction of the obsolete current-phase status header. The header now credits canonical/generated connector work to authoritative Phase 2 and identifies authoritative Phase 3 as intervention design accepted but implementation unapproved.

## Acceptance basis

- Generated or irreversibly anonymised examples only.
- Deterministic, human-owned Core with no AI startup/runtime dependency.
- Tenant/organizational authorization, forced RLS and composite tenant constraints specified.
- Persistent idempotency, ETags, atomic audit/outbox and worker concurrency specified.
- Code/reference-only evidence annotations; prohibited/free-text fields rejected.
- Complete intervention participation in subject-rights lifecycle.
- C3-T01–C3-T40 require direct executable node evidence during implementation.
- Future migration `0009` is additive/self-contained and revisions `0001`–`0008` remain immutable.
- No intervention code, endpoint or migration exists; migrations remain at `0008`.
- Real ERP production approval remains separate and Phase 4 remains prohibited.

## Decision

**Accepted for design.** This review does not authorize implementation. Phase 3 implementation requires the user's separate explicit approval. Phase 4 must not begin.
