# Phase 3 Threat Model

Status: Approved baseline  
Date: 2026-07-29  
Method: STRIDE-informed abuse-case review

## Assets

- tenant-local learner and enrolment records;
- protected institutional and source identifiers;
- academic structure and teaching assignments;
- immutable source observations and lineage;
- reconciliation and subject-rights state;
- authorization, audit, retention, and processing-restriction metadata.

## Trust boundaries

- external client to API;
- future connector to internal observation port;
- Phase 2 identity/tenant context to Phase 3 service authorization;
- service to tenant-required repository;
- runtime role to forced-RLS PostgreSQL;
- ordinary education data to protected identifier/lineage sub-boundary;
- application database to backups/exports.

## Threats and mandatory controls

| ID | Abuse case | Impact | Required control | Required verification |
|---|---|---|---|---|
| P3-T01 | Guess a learner/enrolment UUID in another tenant | Critical disclosure | Tenant context, hidden `404`, composite FKs, forced RLS | API and PostgreSQL cross-tenant tests |
| P3-T02 | Join a local enrolment to a foreign learner/offering | Critical integrity breach | Composite tenant constraints | Invalid relationship integration tests |
| P3-T03 | Platform admin assumes implicit learner access | Critical privilege escalation | No platform-role tenant access | Negative API/security tests |
| P3-T04 | Department role escapes assigned scope | High disclosure/mutation | Derive scope from offering; deny caller scope claims | Horizontal escalation matrix |
| P3-T05 | Viewer enumerates learner rows through lists/counts | High privacy leakage | Aggregate-only viewer policy; bounded authorized lists | Enumeration and response-minimisation tests |
| P3-T06 | Over-post prohibited demographic/health/free-text fields | Critical unlawful collection | Forbid unknown fields and explicit prohibited errors | Contract/property tests |
| P3-T07 | Identifier appears in logs, errors, audit changes, cursor, metrics | High disclosure | Masking and allowlisted telemetry | Capture/redaction tests |
| P3-T08 | Ordinary reader retrieves source keys or unmasked learner reference | High disclosure | Separate permissions, MFA, reason, audit | Negative and positive protected-access tests |
| P3-T09 | Malicious source key causes injection or path traversal | High | Treat as opaque bounded data; parameterized SQL; never file/path use | Adversarial input tests |
| P3-T10 | Future connector submits unauthorized entity type | High integrity breach | Source authority rules and internal port authorization | Source-not-authorized tests |
| P3-T11 | Lower-authority/newer observation overwrites primary fact | High corruption | Deterministic authority before recency | Precedence integration tests |
| P3-T12 | Equal-authority conflict silently resolves | High corruption | Reconciliation issue; no automatic projection change | Conflict tests |
| P3-T13 | Late observation rewrites temporal history | High corruption | Separate observed/effective times; temporal conflict handling | Late/out-of-order tests |
| P3-T14 | Duplicate observation creates duplicate records | High integrity | Source/version uniqueness and persistent idempotency | Replay/race tests |
| P3-T15 | Canonical correction destroys source evidence | High repudiation | Immutable observations/lineage and supersession | Append-only and correction tests |
| P3-T16 | Cross-tenant learner merge creates identity graph | Critical disclosure | Tenant-local merge only; composite constraints; no automatic merge | Cross-tenant merge negatives |
| P3-T17 | Teaching assignment is treated as authorization | High escalation | Explicitly descriptive model; auth from Phase 2 assignments only | Policy unit tests |
| P3-T18 | Processing restriction is bypassed by ordinary mutation/export | High compliance breach | Central restriction check | API/service negative tests |
| P3-T19 | Subject export becomes an unbounded bulk exfiltration path | Critical disclosure | Dedicated permission, MFA, reason, single subject, expiring manifest, audit | Export scope/rate/expiry tests |
| P3-T20 | Retention job deletes held/ineligible lineage | Critical loss/compliance | Eligibility metadata; no physical deletion in Phase 3 | No-delete API test and eligibility rules |
| P3-T21 | Concurrent updates create overlapping versions/enrolments | High corruption | ETags plus PostgreSQL exclusion constraints | Concurrency tests |
| P3-T22 | Cursor reveals identifier/order internals or crosses collection | Medium leakage | Opaque signed/validated cursor bound to route/filter | Cursor tamper/cross-route tests |
| P3-T23 | Idempotency key replays another actor's protected response | Critical disclosure | Actor/tenant/method/concrete-route/key scope and request hash | Cross-actor/tenant replay negatives |
| P3-T24 | Audit outage permits sensitive mutation or unmask | High repudiation | Atomic/fail-closed audit | Audit failure tests |
| P3-T25 | Raw ERP payload is retained accidentally | Critical over-collection | No raw/blob/JSON payload column; allowlisted observation fields | Schema inspection and over-post tests |
| P3-T26 | Backup or generated export outlives retention | High compliance breach | Operational encryption/retention prerequisites; expiring manifest only | Deployment review; artifact storage deferred |

## Security test matrix

For each tenant-owned Phase 3 resource, test:

- list, detail, create, update, transition, lineage, and subject-rights routes;
- same tenant/scope success;
- foreign tenant, foreign campus, and foreign department denial;
- guessed IDs and mismatched parent IDs;
- inactive/suspended membership and stale security epoch;
- role without permission and platform role without membership;
- missing/insufficient MFA and missing reason;
- unknown fields, prohibited fields, Unicode/boundary/adversarial values;
- stale/missing ETags and idempotency conflicts;
- absent tenant context and pooled PostgreSQL connection reuse.

Every threat above must map to an automated test or an explicit operational
verification before Phase 3 acceptance.

## Residual risks

- jurisdiction-specific lawful basis and retention configuration remain deployment
  responsibilities;
- backups and export artifacts require later operational/object-storage designs;
- polymorphic lineage integrity must use concrete link tables or reviewed triggers;
- faculty/student/parent access is excluded rather than assumed safe;
- future connectors add credential, transport, file, SSRF, and ingestion threats in
  Phase 4.

No residual risk authorizes weakening tenant isolation, masking, audit, or prohibited
attribute controls.
