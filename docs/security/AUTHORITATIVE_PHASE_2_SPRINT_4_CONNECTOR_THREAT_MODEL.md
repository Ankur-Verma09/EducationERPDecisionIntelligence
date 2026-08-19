# Authoritative Phase 2 Sprint 4 Connector Threat Model

Status: Design candidate; every applicable case requires an automated negative test.

| ID | Threat | Required control and executable evidence |
|---|---|---|
| C4-T01 | Cross-tenant connector/job access | App authorization, composite keys, forced RLS; API and non-bypass PostgreSQL negatives |
| C4-T02 | Direct canonical-table write | Adapter has no session/model access; dispatcher-only tests and runtime grants |
| C4-T03 | Enabled external connector or SSRF | Closed registry permits mock only; reject URL/host/path fields and verify no egress dependency |
| C4-T04 | Secret ingestion/disclosure | Mock forbids credential refs and secret-shaped config; redaction/log/OpenAPI tests |
| C4-T05 | Executable mapping/SQL injection | Declarative allowlist and extra-forbid; malicious expression/SQL tests |
| C4-T06 | Raw/prohibited learner data retention | Closed schemas, prohibited-field tests, DB inspection and event/log assertions |
| C4-T07 | Duplicate delivery/replay | Persistent unique identities and observation idempotency; restart/concurrency tests |
| C4-T08 | Premature watermark advance | Commit checkpoint with accepted outcomes; forced rollback/resume test |
| C4-T09 | Worker death causes skip/duplication | Lease expiry and durable checkpoint; killed-worker E2E |
| C4-T10 | Poison record blocks batch | Per-record quarantine and valid-record progress test |
| C4-T11 | Late/lower-authority overwrite | Existing effective-time/authority service; late and precedence PostgreSQL tests |
| C4-T12 | Ambiguous learner auto-merge | Reconciliation-only behavior; negative identity-resolution test |
| C4-T13 | Unbounded data/resource exhaustion | Size, batch, concurrency, duration, attempts and retention bounds tests |
| C4-T14 | Quarantine enumeration/value leak | Permission, scope, masking, opaque cursor and safe-error tests |
| C4-T15 | Unsafe replay/substitute payload | MFA, reason, immutable original, idempotency and audit tests |
| C4-T16 | Mapping/config lost update | ETag/row version and concurrent-update tests |
| C4-T17 | Event data leakage or schema drift | Closed envelope/payload models and outbox content inspection |
| C4-T18 | Tenant-less background job | Tenant context required before query; worker fail-closed test |
| C4-T19 | Append-only evidence tampering | PostgreSQL triggers/grants; runtime update/delete negatives |
| C4-T20 | Migration weakens RLS/immutability | Fresh/existing lifecycle and catalog inspection tests |
| C4-T21 | Permission escalation through delegation | Grant-ceiling and role matrix negative API tests |
| C4-T22 | Cursor reuse across tenant/route/filter/time | Signed/bound/expiring opaque cursor negative tests |
| C4-T23 | Idempotency key reused with changed input | Actor/tenant/route/body binding conflict test |
| C4-T24 | Failure affects Core availability | failed jobs remain domain state; live/readiness isolation test |

Residual risk: this design cannot validate a real vendor schema, network, credential, rate limit, or numeric pilot threshold. Those are Sprint 5 entry criteria and remain blocked.

