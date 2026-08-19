# Authoritative Phase 2 Sprint 4 Connector HLD

Status: Design candidate; independently reviewed; implementation requires explicit approval.

## Objective and boundary

Sprint 4 establishes the integration framework with a generated-data mock ERP adapter. It proves safe, resumable ingestion into the already approved canonical education services. It does **not** connect to a real ERP, open an external transport, store a real credential, implement intervention workflows, or add AI capability. Sprint 5 remains the first real ERP connector and is separately gated.

Only generated or irreversibly anonymised examples are permitted. The first implementation enables exactly one adapter kind, `generated_mock_v1`; all REST, SOAP, database, SFTP and file adapters remain disabled.

## Context and components

1. Tenant operator API registers and tests a mock connector and starts a bounded sync job.
2. Connector application service authorizes the tenant, validates configuration, and persists job state.
3. Adapter port emits closed-schema generated records and a deterministic checkpoint.
4. Validation and mapping services reject unknown fields, executable mappings and prohibited attributes.
5. Staging stores only validated generated normalized fields for a short, configurable retention period. Quarantine stores error metadata and source-key fingerprints, never raw source values.
6. Canonical command dispatcher invokes `record_observation`; it never writes canonical tables directly.
7. The same database transaction records job progress, canonical observation/lineage, audit, and the existing version-1 transactional outbox event where applicable.
8. Reconciliation compares input, accepted, rejected, duplicate and projected counts and records deterministic results.

## Trust boundaries

- API boundary: OIDC identity, active tenant membership, explicit permission and scope.
- Adapter boundary: closed Python protocol; no user-provided code, SQL, URL or filesystem path.
- Data boundary: tenant-owned tables with immutable tenant keys, composite references and forced PostgreSQL RLS.
- Canonical boundary: only the canonical service may create observations, lineage and projections.
- Event boundary: existing provider-neutral envelope and outbox; no broker is introduced in Sprint 4.
- Secret boundary: an optional opaque vault reference may be modeled, but the mock connector accepts no credential reference or value.

## Availability and failure behavior

Jobs use durable states (`queued`, `running`, `succeeded`, `failed`, `cancelled`) and batches use durable checkpoints. A checkpoint is acknowledged only after accepted records and job counters commit. Re-executing a batch is idempotent by connector, entity type, source record key/version and mapping version. A poison record is quarantined without blocking valid records. Worker termination before commit causes replay; termination after commit observes the durable checkpoint and does not duplicate or skip records.

No connector failure affects Core live/readiness. Resource limits bound batch size, record size, run duration, retained staging rows and concurrent jobs per tenant.

## Security and privacy invariants

- Generated data only; prohibited learner attributes and arbitrary extensions are rejected.
- No raw payload, secret value, executable expression, network destination or local path is accepted.
- Responses and events expose counts, safe identifiers and error codes only.
- Every mutation uses persistent idempotency; configuration updates use ETags; collections use tenant/route/filter/expiry-bound opaque cursors.
- Replay is audited, requires `connector:replay`, recent MFA and a reason, and reuses the original immutable normalized record.
- Cross-tenant resource identifiers return hidden `404` and cannot be inferred through counts or timing-sensitive error detail.

## Deployment

The framework runs within Core using the existing database and Core resource limits. A separate worker process may be introduced using the same Core image and least-privileged runtime database role; it receives no AI configuration. Sprint 4 adds no new externally reachable service and no external egress requirement.

## Exit criteria

- Generated valid, invalid, duplicate and late records sync and reconcile deterministically.
- Invalid records quarantine without blocking valid records.
- Killed-worker resume proves no duplicate or skipped committed record.
- Direct canonical-table writes are structurally and executably prohibited.
- Unit, PostgreSQL, API, security and E2E tests plus migration, quality, image, scan and smoke gates pass.
- Governance and independent completion review remain current.

