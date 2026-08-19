# Authoritative Phase 2 Sprint 5 — Demo ERP Connector Data Model

Status: **Approved for generated demo-only design; additive revision `0008` remains
unimplemented pending separate implementation approval.**

Revision `0008` will be self-contained and additive; `0001`–`0007` remain immutable.

| Table/change | Concrete demo fields and constraint |
|---|---|
| `connector_source_schemas` | tenant, connector, package id=`synthetic-reference-erp-v1`, package version=`1.0.0`, schema version=`1`, schema SHA-256, status, timestamps |
| mapping version extension | composite source-schema reference plus identity, authority and threshold version=`1` |
| `connector_transport_configs` | kind=`in_process_csv_test_double`, egress=false, credential=null, page/record/batch/time/retry bounds |
| credential references | remain database-disabled for this adapter |
| job/batch extension | package/schema/threshold snapshot, explicit test clock, simulated failure code and freshness watermark |
| staging extension | source/effective timestamps, minimised document, landing/quarantine expiry class |
| reconciliation extension | completeness/freshness/rejection/duplicate/unresolved/variance measurements and breach codes |
| schema drift evidence | immutable expected/actual fingerprint and safe code; no record value |

All tenant relationships are composite; tenant identifiers are immutable; RLS is
enabled/forced; evidence is append-only; runtime grants are least privilege. Checks
enforce the single adapter/transport, no credential/egress, landing <=24 hours and
quarantine <=7 days. IDs remain UUIDs and public pagination remains opaque/bound.

Required gates: `0007 -> 0008 -> 0007 -> 0008`, `base -> head`, catalog/RLS/grant/
trigger inspection, non-bypass tenant/mutation negatives and checksum proof that
`0001`–`0007` did not change.
