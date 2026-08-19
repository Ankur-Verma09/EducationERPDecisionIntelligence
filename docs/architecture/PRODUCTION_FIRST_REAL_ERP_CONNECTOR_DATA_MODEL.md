# Production First Real ERP Connector data model

Status: **Blocked design; no migration authorized.**

The accepted demo tables may be generalized only through a future additive migration.
The design must preserve tenant-composite keys, forced RLS and append-only evidence.

| Required record | Required production binding |
|---|---|
| source package | package id/version, vendor/product/version, source release, checksums, approval state |
| endpoint policy | transport kind, destination/port/path allowlist, TLS policy, data region |
| credential reference | secret-provider id and opaque key reference; never secret material |
| source schema | object/stream, schema version/hash, fields, types, keys and change semantics |
| mapping version | complete source disposition, canonical target, transforms and policy versions |
| authority version | per-entity/per-field source rank and effective interval |
| identity version | stable keys, normalization, ambiguity and merge prohibitions |
| privacy version | classification, landing/quarantine retention, masking, deletion and rights handling |
| threshold version | numeric completeness, freshness, rejection, duplicate and reconciliation gates |
| job evidence | immutable snapshots, checkpoint, attempts, failure class and reconciliation result |

Database constraints must reject unapproved package states, non-read-only transports,
unbounded retention, cross-tenant references and activation without all required owner
approvals. Exact columns and revision number remain unapproved until concrete values
and compatibility requirements are reviewed.
