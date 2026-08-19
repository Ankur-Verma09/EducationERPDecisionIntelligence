# Production First Real ERP Connector threat model

Status: **Blocked pending transport-specific review.**

| Threat | Mandatory control/evidence |
|---|---|
| cross-tenant access | application authorization, composite FKs, forced RLS and non-bypass PostgreSQL negatives |
| source write or privilege escalation | read-only source account, adapter without write methods, source-side audit evidence |
| SSRF/network pivot | fixed destination/port allowlist, DNS/IP rebinding defense and network egress policy tests |
| credential leakage | opaque references, worker-only injection, rotation/revocation and API/log/event/database scans |
| MITM/TLS downgrade | transport-specific certificate/host verification and downgrade negatives |
| schema drift/data poisoning | checksum-bound closed schemas, size/type limits, formula/archive/parser abuse tests |
| child-data overcollection | field allowlist, prohibited-attribute rejection and persistence/log negatives |
| identity collision | stable-key rules, ambiguity reconciliation and no-auto-merge tests |
| authority/late-arrival corruption | precedence/effective-time rules and PostgreSQL non-overwrite evidence |
| retry storm/source overload | bounded concurrency, attempts/backoff/jitter, rate-limit and circuit-breaker tests |
| duplicate/skip | transactional checkpoint, idempotency and kill/resume tests |
| over-retention/rights failure | DB retention bounds, purge/hold/export/delete and backup-handling tests |
| evidence tampering | append-only grants/triggers, audit/outbox integrity and runtime mutation negatives |
| Core/AI coupling | source outage with Core healthy; connector cannot access AI or trigger intervention |
| supply-chain/package substitution | signature/checksum verification, SBOM, provenance, scans and approval-state gate |

SFTP, REST/API, CSV managed transfer and read-replica each require additional specific
threat cases. No selection may be inferred from the demo test double.
