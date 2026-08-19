# Implemented API: Phase 2 Sprint 4 Generated Mock Connector

The implementation exposes the approved tenant routes under `/api/v1`:

- `POST/GET /tenants/{tenant_id}/connectors`
- `GET/PATCH /tenants/{tenant_id}/connectors/{connector_id}`
- `POST /tenants/{tenant_id}/connectors/{connector_id}/test`
- `POST /tenants/{tenant_id}/sync-jobs`
- `GET /tenants/{tenant_id}/sync-jobs/{job_id}`
- `GET /tenants/{tenant_id}/connectors/{connector_id}/runs`
- `GET /tenants/{tenant_id}/reconciliation-runs/{run_id}`
- `GET /tenants/{tenant_id}/sync-jobs/{job_id}/quarantine`
- `POST /tenants/{tenant_id}/dead-letters/{dead_letter_id}/replay`

Only `generated_mock_v1` and the `valid`, `mixed`, `duplicates`, and `late`
generated scenarios are accepted. Request models reject extra fields, including
URLs, paths, credentials and uploaded payloads. Mutations use persistent
`Idempotency-Key`; connector updates use `If-Match`; lists use signed,
tenant/route/filter/expiry-bound opaque cursors. Replay requires the dedicated
permission, MFA and a bounded audited reason.

Lifecycle events use the existing version-1 envelope and transactional outbox:
`connector.sync_started`, `connector.batch_validated`,
`connector.sync_completed`, and `connector.sync_failed`. Payloads contain safe
identifiers, state and counts only.

