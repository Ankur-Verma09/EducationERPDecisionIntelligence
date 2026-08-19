# Authoritative Phase 3 — Core Intervention Workflow Threat Model

Status: Independently accepted design; implementation not approved  
Date: 2026-08-05  
Method: STRIDE-informed abuse cases

## Assets and trust boundaries

Assets are tenant-local cases, ownership, tasks, deadlines, structured evidence/annotations, outcomes, audit, subject-rights state and safe reporting. Boundaries are client/API, identity-to-policy, policy-to-service, Core-to-forced-RLS PostgreSQL, scheduler/worker-to-Core, outbox-to-consumer, ordinary-to-restricted content, and Core-to-future AI. PostgreSQL is never accessible to AI.

## Automated negative-security matrix

| ID | Abuse case | Mandatory control | Required automated evidence |
|---|---|---|---|
| C3-T01 | Guess foreign-tenant case/task UUID | hidden 404, RLS, composite FK | API + PostgreSQL two-tenant tests |
| C3-T02 | Attach foreign learner/department/user | composite tenant keys and active membership | integration negatives |
| C3-T03 | Platform admin reads cases | no implicit tenant access | API negative |
| C3-T04 | Staff escapes campus/department | server-derived scope | role/scope matrix |
| C3-T05 | Assignee reads unrelated case | explicit case/task grant only | horizontal IDOR test |
| C3-T06 | Caller supplies broader scope | ignore/reject caller claims | schema/policy test |
| C3-T07 | Suspended member retains access | security epoch + membership status | stale-token negative |
| C3-T08 | Delegation grants excess permission | subset and scope enforcement | delegation negative |
| C3-T09 | Invalid state transition | closed deterministic table | property/state tests |
| C3-T10 | Concurrent transition loses update | ETag/CAS and row lock | PostgreSQL race test |
| C3-T11 | Replay duplicates mutation/event | persistent idempotency + outbox atomicity | restart/race replay test |
| C3-T12 | Actor replays another actor response | actor/tenant/route/hash binding | cross-actor negative |
| C3-T13 | Silent owner removal | exactly one active owner + history | constraint/service test |
| C3-T14 | Escalation grants access or auto-owner | proposal-only escalation | scheduler policy test |
| C3-T15 | Scheduler duplicates breach | unique step/due + SKIP LOCKED | concurrent worker test |
| C3-T16 | Clock/time-zone manipulation | server UTC + immutable policy/calendar | boundary/late test |
| C3-T17 | Close with required open tasks | deterministic close guard | API state negative |
| C3-T18 | Annotation/evidence smuggles prohibited data | code/reference-only schema and database constraints | adversarial/property test |
| C3-T19 | URL/blob/raw ERP payload creates exfiltration | no URL/blob/raw fields | OpenAPI/schema inspection |
| C3-T20 | Learner display identifier, source key or prohibited value leaks in logs/errors/events | allowlisted telemetry/event payload | capture/redaction test |
| C3-T21 | Evidence/history is altered/deleted | append-only DB trigger/grants | PostgreSQL runtime-role test |
| C3-T22 | Processing restriction bypass | central restriction guard | create/export/notify negatives |
| C3-T23 | Subject export crosses learner/tenant | single-subject bound export, MFA + closed reason code | API/security test |
| C3-T24 | Aggregate report exposes small cohort | suppression and scoped dimensions | inference-boundary test |
| C3-T25 | Cursor crosses tenant/route/filter | opaque bound cursor | tamper/cross-context tests |
| C3-T26 | Missing audit still commits action | atomic fail-closed audit | fault-injection test |
| C3-T27 | Notification event leaks learner/contact | safe UUID/code payload only | serialized payload test |
| C3-T28 | Notification consumer changes case | consumer lacks Core write path | integration permission test |
| C3-T29 | AI outage blocks Core | no AI import/config/startup dependency | Core-only and stop-AI E2E |
| C3-T30 | AI writes DB or transitions case | no DB credential/network; API auth; human actor | compose/API negatives |
| C3-T31 | AI-generated evidence treated as fact | future source label + human acceptance; absent now | endpoint absence/contract test |
| C3-T32 | Migration weakens RLS/history controls | self-contained additive `0009`, immutable prior hashes | lifecycle/schema/grant tests |
| C3-T33 | Type mutation changes workflow semantics | type immutable; cancel/recreate | API/schema/history negative |
| C3-T34 | Scope widening exposes existing content | narrowing only; most-restrictive historical envelope | scope-widen/move negatives |
| C3-T35 | Scope mutation races grant revocation | lock and re-evaluate membership/scope in transaction | PostgreSQL TOCTOU race |
| C3-T36 | Priority change rewrites SLA history | append-only attribute history; no implicit rebind | API/history/SLA assertions |
| C3-T37 | SLA rebind backdates, shortens, or follows breach | active state; no breach; new deadline `> now` and `>= current`; MFA + closed reason code | state/deadline/breach negatives |
| C3-T38 | Rights correction overwrites attestation | append-only supersession links | API/PostgreSQL negatives |
| C3-T39 | Rights completion skips case disposition/legal hold | per-case closed disposition before completion | completion/hold negatives |
| C3-T40 | Restriction misses read/worker/projection path | central transactional restriction propagation | API, scheduler, projection E2E |

## Security acceptance rules

Every C3-T01–C3-T40 identifier must map to one or more executable test node IDs. No evidence row may be satisfied only by another traceability document. Tests must exercise non-superuser `NOBYPASSRLS` PostgreSQL, pooled-connection tenant reset, absent tenant context, role/permission/scope combinations, missing/stale ETags, idempotency conflicts, malformed Unicode/boundaries, audit failure and worker concurrency.

## Privacy and operational controls

- Generated or irreversibly anonymised data only in development/tests.
- No production retention values are inferred; deployment fails closed without approved policy.
- No binary/object store, outbound notification delivery or AI service is introduced.
- Export is metadata manifest only; artifact encryption, expiry and backup deletion remain deployment prerequisites.
- Audit/event/log content uses tenant-safe IDs and closed codes, never learner display identifiers, source keys or prohibited values.

## Residual risks

Real ERP semantics, production legal basis/retention, notification channels, object storage and AI evidence are unresolved future approvals. These do not prevent deterministic generated-data Phase 3 implementation after design approval, but they block production activation of those surfaces. No residual risk permits weaker tenant isolation, human ownership or audit.
