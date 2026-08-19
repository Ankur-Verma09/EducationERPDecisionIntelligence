# Production First Real ERP Connector LLD

Status: **Blocked — parameter binding and approval evidence absent.**

## Required interfaces

- `probe()`: authenticate and verify read scope without importing records.
- `read_page(stream, checkpoint, limit)`: return bounded immutable source records and
  the next opaque checkpoint; no arbitrary query, path or URL input.
- `close()`: release transport resources. No create/update/delete/write-back method.

The approved package must bind connection timeout, page and byte limits, concurrency,
retry classes, maximum attempts, jitter/backoff, rate limit handling, freshness clock,
snapshot/isolation behavior and recovery-point semantics. Defaults are forbidden.

## Processing sequence

1. Claim a tenant job and load immutable package/schema/mapping/authority/identity/
   privacy/threshold snapshots.
2. Resolve an allowlisted endpoint and opaque secret reference from deployment policy.
3. Establish the approved authenticated/TLS connection and prove read-only scope.
4. Read one bounded page; validate source version, shape, size and prohibited fields.
5. Minimise and classify landing/quarantine data under package retention rules.
6. Apply only checksum-bound declarative mappings.
7. Resolve stable identity; ambiguous or conflicting matches never auto-merge.
8. Call existing canonical observation/reconciliation services.
9. Commit outcomes, audit, outbox and checkpoint atomically.
10. At source exhaustion, calculate package-defined gates and block on breach.

All error responses and events use closed codes and safe identifiers/counts only.
Transport-specific behavior cannot be completed until the missing package is supplied.
