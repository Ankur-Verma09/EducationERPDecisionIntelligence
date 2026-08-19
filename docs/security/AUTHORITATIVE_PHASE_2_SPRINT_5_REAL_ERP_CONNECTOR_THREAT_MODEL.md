# Authoritative Phase 2 Sprint 5 — Demo ERP Connector Threat Model

Status: **Approved for generated demo-only design; not production or implementation approval.**

| ID | Demo threat | Required automated evidence |
|---|---|---|
| C5-T01 | Cross-tenant connector/data access | Authorization, composite keys, forced RLS and non-bypass PostgreSQL negatives |
| C5-T02 | Network/SSRF escape | In-process adapter opens no socket; reject URL/path/host fields; egress-isolation test |
| C5-T03 | Source write | Adapter exposes no write method; interface and call-trace negatives |
| C5-T04 | Credential disclosure | API/config reject credentials and secret references; log/event/API inspection |
| C5-T05 | TLS downgrade | Not applicable because no transport exists; reject TLS/transport override fields |
| C5-T06 | Schema drift | Fingerprint gate fails closed, emits safe event and makes no canonical mutation |
| C5-T07 | Malicious/formula values | Closed typed schema, Unicode/size limits and generated attack fixtures |
| C5-T08 | Prohibited child attribute | Allowlist/minimisation plus DB/log/event negative inspection |
| C5-T09 | Identity collision/merge | Exact tenant/source/key rule, reconciliation on ambiguity, no automatic merge |
| C5-T10 | Authority/late correction | Versioned authority and temporal non-overwrite PostgreSQL tests |
| C5-T11 | Duplicate/skip on outage | Durable checkpoint, idempotency and committed kill/resume tests |
| C5-T12 | Retry storm | One tenant job, three attempts, 1/2/4-second backoff and deterministic outage test |
| C5-T13 | Unbounded extract | 100/page, 64 KiB/record, 5 MiB/batch and 15-second read limits |
| C5-T14 | Over-retention | Landing <=24h, quarantine <=7d, cleanup and subject-rights tests |
| C5-T15 | Quarantine enumeration | Scoped permission, masking, hidden 404 and bound-cursor tests |
| C5-T16 | Threshold manipulation | Immutable version, MFA/reason/ETag/idempotent activation tests |
| C5-T17 | Unsafe mapping activation | Schema binding, dry run and lost-update tests |
| C5-T18 | Event/log leakage | Closed payload schemas and generated sensitive-marker scan |
| C5-T19 | Tenant-less worker | Mandatory tenant context and fail-closed worker test |
| C5-T20 | Evidence tampering | Append-only triggers/grants and runtime update/delete negatives |
| C5-T21 | Core coupled to adapter | Transport-outage scenario while Core live/readiness remain healthy |
| C5-T22 | Package/policy substitution | Manifest checksum and approved demo-profile checksum gate |
| C5-T23 | Supply chain | Pinned dependencies, SBOM, license, image and secret scans |
| C5-T24 | Real data introduced | Generated provenance and repository fixture-content scan |

All 24 cases are applicable to the demo except C5-T05, whose negative replacement
is mandatory. Passing this model approves only generated, local demo execution; a
real connector requires a new transport-specific threat model and production owner
approvals.
