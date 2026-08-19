# Authoritative Phase 2 Sprint 5 — Demo ERP Connector LLD

Status: **Approved for generated demo-only design; not production or implementation approval.**

## Modules and contracts

Planned modules are `connectors.adapters.synthetic_reference_erp_v1`,
`connectors.package`, `connectors.schema`, existing mapping/identity/worker/
reconciliation services, connector persistence and connector APIs.

`read_batch(checkpoint, limit) -> AdapterBatch` reads only checksum-valid package
records or one named generated scenario. The transport opens no socket and accepts
no external path. Limits are 100 records/page, 64 KiB/record, 5 MiB/batch,
15-second read, three attempts with 1/2/4-second backoff, and one concurrent tenant
job. Write operations do not exist.

## Processing

1. Claim a tenant job with `FOR UPDATE SKIP LOCKED`.
2. Load immutable package/schema/mapping/authority/identity/threshold versions.
3. Verify manifest SHA-256 values and source schema fingerprint.
4. Read a bounded page and validate closed schemas and prohibited attributes.
5. Retain minimised staging for <=24 hours; quarantine metadata/documents for <=7 days.
6. Apply only approved declarative transforms from `pilot_matrices.xlsx`.
7. Resolve exact stable source identity; ambiguity becomes reconciliation.
8. Dispatch the nine canonical entities through `record_observation`.
9. Commit outcomes, audit, safe outbox events and checkpoint atomically.
10. At exhaustion, evaluate the version-1 mock thresholds and block on breach.

## Drift, correction and failure

Unknown package/schema checksum stops with `source_schema_unsupported`; no guessing.
Corrections require a new source version/effective time. Late conflicting records
cannot overwrite the current projection. Validation and identity ambiguity are
terminal per record. Generated timeout/throttle simulations use bounded retries;
poison failures use immutable staging/dead-letter replay. Core readiness is isolated.

The explicit test clock makes freshness deterministic. All constants are demo-only.
