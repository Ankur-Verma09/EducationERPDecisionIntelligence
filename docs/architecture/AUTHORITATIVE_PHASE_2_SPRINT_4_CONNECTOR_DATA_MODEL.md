# Authoritative Phase 2 Sprint 4 Connector Data Model

Status: Planned for additive Alembic revision `0007`; revisions `0001`-`0006` are immutable.

Every table below has `tenant_id NOT NULL`, immutable tenant enforcement, composite tenant foreign keys, forced RLS and runtime-role grants limited to required operations.

| Table | Purpose and principal fields |
|---|---|
| `connectors` | `id`, name, kind=`generated_mock_v1`, status, config document, version, created/updated metadata |
| `connector_credential_refs` | Optional opaque vault reference metadata; Sprint 4 forbids rows for mock connectors and stores no secret values |
| `mapping_sets` | Stable mapping identity per connector/entity scope |
| `mapping_versions` | Immutable version, closed declarative mapping document, schema version, checksum, activation metadata |
| `sync_jobs` | Connector/mapping snapshot, requested-by, state, lease, attempt, bounded counters, start/end timestamps, failure code |
| `connector_watermarks` | Last acknowledged opaque checkpoint per connector/entity stream with version |
| `connector_batches` | Job sequence, checkpoint before/after, state and counters |
| `staging_records` | Generated normalized document, source-key fingerprint, versions/times, validation state, expiry; never raw payload |
| `connector_validation_errors` | Safe code, field path, rule version and staging reference; no rejected value |
| `reconciliation_runs` | Input/valid/rejected/duplicate/applied/reconciled totals, threshold snapshot and disposition |
| `connector_dead_letters` | Safe failure category, staging reference, attempt metadata and replay state; no payload copy |

## Constraints

- Connector kind check permits only `generated_mock_v1` in revision `0007`.
- Configuration JSON is schema-validated in application code and database size-bounded; URLs, paths, SQL and credential material are forbidden keys.
- Mapping versions and completed batch outcomes are append-only by PostgreSQL trigger.
- Partial unique index permits one `queued`/`running` job per connector.
- Timestamps are timezone-aware; counters and sequence numbers are non-negative.
- Staging expiry is mandatory and bounded by deployment policy.
- Source keys are tenant-bound fingerprints; raw keys live only transiently inside the request transaction and existing protected lineage mechanisms.
- All identifiers are UUIDs; public lists use opaque cursors, not database offsets.

## Migration lifecycle

`0007` is self-contained and imports no ORM metadata. Required gates are fresh `base -> 0007`, existing `0006 -> 0007`, downgrade `0007 -> 0006`, and re-upgrade `0006 -> 0007`, with schema/constraint/RLS inspection under migration-owner and non-bypass runtime roles.

