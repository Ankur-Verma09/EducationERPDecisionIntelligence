# Authoritative Phase 2 Sprint 4 Connector API and Event Contract

Status: Design candidate. Base path is `/api/v1/tenants/{tenant_id}`.

## Permissions

Add `connector:read`, `connector:manage`, `connector:run`, `connector:reconcile`, and `connector:replay`. `tenant_owner` receives all; `registrar` receives read/run/reconcile/replay; `auditor` receives read-only. Delegation cannot grant permissions the actor lacks. Replay requires recent MFA and a non-empty bounded reason.

## Endpoints

| Method and path | Permission | Contract |
|---|---|---|
| `POST /connectors` | `connector:manage` | Create `generated_mock_v1`; persistent `Idempotency-Key`; rejects transport/secret fields |
| `GET /connectors` | `connector:read` | Bounded list with opaque bound cursor |
| `GET /connectors/{connector_id}` | `connector:read` | Safe config and health summary; no secret material |
| `PATCH /connectors/{connector_id}` | `connector:manage` | Closed update, `If-Match`, idempotency |
| `POST /connectors/{connector_id}/test` | `connector:run` | Runs only deterministic local contract validation; idempotency |
| `POST /sync-jobs` | `connector:run` | Starts bounded job for connector and fixture scenario; idempotency |
| `GET /sync-jobs/{job_id}` | `connector:read` | State, safe counters and timestamps |
| `GET /connectors/{connector_id}/runs` | `connector:read` | Opaque-cursor run history |
| `GET /reconciliation-runs/{run_id}` | `connector:reconcile` | Counts, threshold snapshot and disposition |
| `GET /sync-jobs/{job_id}/quarantine` | `connector:reconcile` | Safe error metadata only, opaque cursor |
| `POST /dead-letters/{dead_letter_id}/replay` | `connector:replay` | MFA, reason, original mapping version, idempotency; never accepts replacement payload |

All request/response models forbid extra fields. Mutation responses replay exactly across process restarts. Cross-tenant and undisclosable resources return `404`. Rate, page, batch and string sizes are server bounded.

## Event envelope

Events use the existing `EventEnvelope` fields: `event_id`, `event_type`, `aggregate_id`, `tenant_id`, `occurred_at`, `schema_version="1"`, `trace_id`, and `payload`. Event types are:

- `connector.sync_started`
- `connector.batch_validated`
- `connector.sync_completed`
- `connector.sync_failed`

Payloads contain connector/job/batch UUIDs, fixture scenario identifier, safe counts, status and stable failure code only. They contain no learner identifier, source key, normalized record, error value, credential reference, reason text or arbitrary extension. Events are written to the existing transactional outbox; publication infrastructure is not part of Sprint 4.

## Reconciliation thresholds for generated fixtures

Thresholds are deterministic test-contract values, not pilot acceptance thresholds: completeness 100% of fixture rows accounted for; freshness measured against the fixture clock; zero unexplained count variance; expected rejection and duplicate totals exactly match the scenario manifest. These values cannot be carried into Sprint 5 without source-owner approval.

