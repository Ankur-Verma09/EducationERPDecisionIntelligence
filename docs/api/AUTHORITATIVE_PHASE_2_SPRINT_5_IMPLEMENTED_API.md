# Authoritative Phase 2 Sprint 5 — Implemented Demo Connector API

Status: **Implementation candidate pending independent completion review.**

The existing connector endpoints now accept the closed
`synthetic_reference_erp_v1` kind only with package version `1.0.0` and one of the
ten approved generated scenarios. Request models reject URL, host, filesystem path,
upload, credential, TLS override and arbitrary configuration fields.

## Endpoints

- `POST /api/v1/tenants/{tenant_id}/connectors` creates the demo connector and its
  immutable source-schema, transport, mapping, authority and policy snapshots.
- `POST /api/v1/tenants/{tenant_id}/connectors/{connector_id}/test` verifies the
  compiled approval-root hash, manifest/file checksums, schema dispositions and
  no-network/no-credential policy without importing records.
- `POST /api/v1/tenants/{tenant_id}/sync-jobs` executes bounded generated ingestion
  with an optional deterministic `test_clock` and frozen version snapshots.
- Existing connector/job/run/quarantine/reconciliation/dead-letter endpoints retain
  persistent idempotency, ETags, MFA/recent authentication, hidden tenant resources,
  safe metadata and bound opaque cursors.

Successful demo jobs emit `connector.package_verified.v1`,
`connector.sync_started.v1`, `connector.batch_validated.v1` and
`connector.sync_completed.v1`. Threshold failures additionally emit
`connector.threshold_breached.v1` and end in failed/blocked state. Payloads contain
safe IDs, versions, counts and codes only.

No endpoint accepts a real ERP location or credential, performs write-back, starts
an intervention, or invokes an AI service. Production owner approvals remain absent.

