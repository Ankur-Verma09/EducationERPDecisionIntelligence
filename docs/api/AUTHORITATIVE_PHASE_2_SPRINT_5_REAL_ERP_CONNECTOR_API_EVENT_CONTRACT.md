# Authoritative Phase 2 Sprint 5 — Demo ERP Connector API/Event Contract

Status: **Approved for generated demo-only design; not production or implementation approval.**

## Closed API profile

Existing Sprint 4 authorization, hidden-404 tenancy, ETags, opaque cursors and
persistent idempotency remain mandatory. The demo adds only the closed connector
kind `synthetic_reference_erp_v1` and package version `1.0.0`.

- `POST /tenants/{tenant_id}/connectors` accepts `name`, the fixed kind/version and
  an optional generated scenario. It rejects URLs, hosts, paths, uploads,
  credentials, arbitrary configuration and unknown fields.
- `POST /connectors/{connector_id}/test` verifies manifest checksums, source schema
  fingerprints and the no-network/no-credential policy. It imports no records.
- `POST /sync-jobs` queues bounded asynchronous processing against an explicit test
  clock and immutable package, schema, mapping, identity, authority and threshold
  version snapshots.
- Existing job/run/quarantine/reconciliation/dead-letter reads expose only safe
  counts, IDs and codes.
- Any demo activation endpoint requires `connector:manage`, recent MFA, reason,
  dry-run reconciliation evidence, `If-Match` and persistent idempotency.

Allowed scenarios are exactly `valid`, `schema-drift-extra-field`,
`prohibited-child-attribute`, `duplicate-version`, `ambiguous-identity`,
`late-correction`, `transport-timeout`, `transport-throttled`,
`credential-rejected` and `oversized-record`. The nine non-`valid` values are the
checksum-controlled IDs in `scenarios/negative_scenarios.json`; aliases and unknown
values are rejected.

## Errors and events

Closed safe errors are `package_checksum_mismatch`, `source_schema_unsupported`,
`mapping_invalid`, `identity_ambiguous`, `record_too_large`,
`prohibited_attribute`, `transport_unavailable`,
`freshness_threshold_breached`, `completeness_threshold_breached` and
`reconciliation_threshold_breached`. Responses never contain source rows, stable
source keys, personal identifiers, paths or environment details.

Versioned envelopes retain tenant, event, aggregate, correlation, causation,
occurred-at and schema-version metadata. Frozen demo event types are
`connector.package_verified.v1`, `connector.schema_drift_detected.v1`,
`connector.sync_started.v1`, `connector.batch_validated.v1`,
`connector.threshold_breached.v1`, `connector.sync_completed.v1` and
`connector.sync_failed.v1`. Payloads contain only safe IDs, version snapshots,
counts, durations and closed codes. No event triggers intervention, ERP write-back
or AI processing.
