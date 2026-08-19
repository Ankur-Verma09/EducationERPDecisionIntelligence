# Independent Design Review: Authoritative Phase 2 Sprint 4

Date: 2026-08-05  
Decision: **Accepted as a design candidate; implementation awaits explicit user approval.**

## Scope reviewed

The HLD, LLD, data model, API/event contract, threat model and implementation plan were checked against the local Engineering HLD, ERP Migration and Integration Plan, Development System Design, Implementation Backlog, existing canonical services, revision `0006`, event envelope/outbox contract and governance.

## Findings and disposition

1. Phase ambiguity: resolved. The latest local engineering sequence places the integration framework/mock connector and first real connector in authoritative Phase 2; intervention is Phase 3 and AI is Phase 4.
2. Missing pilot inputs: not bypassed. The design enables only generated mock data; real connector work remains Sprint 5 and blocked.
3. Premature transport/secret surface: resolved by a closed `generated_mock_v1` registry, no external egress and rejection of credential/URL/path/SQL fields.
4. Canonical integrity: resolved by requiring all accepted records to traverse the existing observation/authority/lineage service and forbidding adapter database access.
5. Resume correctness: addressed with durable lease, transactional batch outcomes and post-commit checkpoint acknowledgement; implementation must prove kill/resume behavior.
6. Privacy and event leakage: addressed by closed generated schemas, short-lived normalized staging, fingerprint-only quarantine metadata and count-only events.
7. Acceptance-threshold confusion: resolved by labeling fixture assertions as test-contract values that cannot authorize Sprint 5 thresholds.
8. Security completeness: C4-T01-C4-T24 supply direct executable acceptance targets, including non-bypass RLS, delegation, cursor and idempotency negatives.

## Approval conditions

Implementation is acceptable only after explicit user approval of this exact package. Any attempt to enable a real transport, accept customer data/credentials, change phase scope, or introduce intervention/AI services requires a new design and approval. Completion requires an independent evidence review after all gates run.

## Independent implementation review — 2026-08-05

Decision: **Rework required; Sprint 4 is not accepted.**

The review detected a PostgreSQL batch-trigger conflict, direct pre-service learner
insertion, and learner-only dispatch that the initial SQLite-heavy connector tests
missed. Those three defects were remediated: a real non-bypass PostgreSQL API sync
now passes, batch evidence becomes immutable after its controlled completion
transition, and all nine approved entity types project through
`record_observation` callbacks. Quarantine queries and cursors are also bound to the
specific job/connector, and replay now checks recent authentication in addition to
MFA.

Acceptance remains blocked by:

1. worker execution is still synchronous and single-transaction rather than a
   durable per-batch `SKIP LOCKED` claim/resume loop;
2. dead-letter creation and immutable-record replay are not functional end to end;
3. revision `0007` lacks the approved `mapping_sets` table, composite tenant foreign
   keys, complete tenant-key immutability, and full append-only runtime grants;
4. expired generated staging cleanup is not implemented;
5. direct executable cases remain incomplete for actual replay/recent-auth/audit,
   tenant-less worker failure, runtime evidence mutation, delegation ceiling,
   connector failure/Core health, and committed-batch worker recovery;
6. the images/scans built before the review remediation no longer validate the
   current source and must be rebuilt after blockers close;
7. because revisions `0001`-`0006` are untracked, byte immutability cannot be proven
   from Git history; a trusted baseline/checksum is still required.

Real ERP transports, credentials, pilot mappings/thresholds, intervention workflows
and Phase 4 AI remain correctly excluded and are not Sprint 4 blockers.

## Final remediation re-review — 2026-08-05

Decision: **Accepted.**

The final implementation closes all prior findings: C4-T11 executes the real late
connector path and proves the current projection is not overwritten while a
`source_conflict` issue is created; C4-T07-C4-T09 identify committed same-job
recovery; C4-T18 identifies tenant-less worker failure; C4-T19 identifies runtime
evidence mutation/delete rejection; C4-T21 identifies delegation-ceiling coverage;
and C4-T24 identifies connector failure with Core readiness preserved. The review
also verified the PostgreSQL nine-entity journey, worker-created dead-letter replay
from immutable normalized input, mapping sets, composite requester membership,
tenant/RLS enforcement and cleanup. No Sprint 4 acceptance blocker remains.
