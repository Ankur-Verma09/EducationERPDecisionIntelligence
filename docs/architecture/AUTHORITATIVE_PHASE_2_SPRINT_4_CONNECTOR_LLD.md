# Authoritative Phase 2 Sprint 4 Connector LLD

Status: Design candidate; no implementation authorization implied.

## Module layout

Planned modules are `education_erp.connectors.contracts`, `adapters.generated_mock`, `mapping`, `validation`, `service`, `worker`, `reconciliation`, `persistence.connector_models`, and `api.connectors`. Adapter and dispatcher ports are dependency-injected so unit tests cannot require external infrastructure.

## Closed contracts

`ConnectorAdapter.read_batch(checkpoint, limit) -> AdapterBatch` returns `records`, `next_checkpoint`, and `source_exhausted`. `AdapterRecord` contains `entity_type`, `source_record_key`, `source_record_version`, `observed_at`, `effective_at`, and a closed typed entity document. `limit` is server-bounded. The adapter cannot receive a database session or canonical model.

The enabled adapter registry is immutable at runtime and contains only `generated_mock_v1`. Unknown kinds fail before persistence. The generated adapter accepts a named fixture scenario and seed, not uploaded content.

## Processing algorithm

1. Lock the queued job with `FOR UPDATE SKIP LOCKED`; set its lease and `running` state.
2. Load the active connector, immutable mapping version and last acknowledged watermark under tenant context.
3. Read at most the configured server maximum from the mock adapter.
4. Validate envelope, entity allowlist, field schema, sizes, timestamps and prohibited attributes.
5. Persist a batch and safe per-record staging/quarantine result. A rejected row does not invoke canonical services.
6. Transform valid records through declarative field mappings restricted to rename, constant-from-allowlist, enum map and ISO date normalization. No expression evaluator is present.
7. Resolve the target using explicit source-key equivalence. Ambiguous identity creates reconciliation; automatic learner merge is forbidden.
8. Call `record_observation` for the nine approved entity types: `academic-period`, `programme`, `programme-version`, `course`, `course-version`, `offering`, `learner`, `programme-enrolment`, and `offering-enrolment`.
9. Enqueue safe connector lifecycle events and audit within the transaction.
10. Commit counters and watermark only after all accepted commands in the batch are durable. On rollback the lease expires and the batch is retried.
11. At exhaustion, calculate reconciliation and complete or fail the job according to configured mock acceptance thresholds.

## State and concurrency

- One active job per connector is enforced in PostgreSQL with a partial unique index.
- Job claims use a lease owner and expiry; stale leases are recoverable.
- Batch identity is unique on `(tenant_id, job_id, sequence_number)`.
- Staging identity is unique on `(tenant_id, connector_id, entity_type, source_key_fingerprint, source_record_version, mapping_version_id)`.
- Counters are derived from persisted record outcomes and checked against non-negative constraints.
- Connector updates use integer version and `If-Match`; mutation replay uses the existing persistent idempotency store.

## Validation and late arrival

Schemas use Pydantic `extra=forbid`, Unicode/length limits and timezone-aware timestamps. Late arrival is not silently discarded: the existing authority/effective-time reconciliation service decides equivalence, application or reconciliation. A lower-authority or ambiguous observation cannot overwrite a higher-authority projection.

## Error model

Public errors use existing request IDs and stable codes: `connector_kind_not_enabled`, `invalid_connector_config`, `sync_already_active`, `mapping_invalid`, `record_quarantined`, `checkpoint_conflict`, and generic hidden `not_found`. Internal exceptions and values are redacted. Retry classification is explicit; validation failures are terminal per record, while lease/database transient failures retry with bounded attempts.

## Cleanup

A tenant-scoped maintenance operation deletes expired generated staging documents after the configured short retention and retains minimized audit, counters, fingerprints and reconciliation metadata per policy. Cleanup must not delete canonical observations or lineage.

