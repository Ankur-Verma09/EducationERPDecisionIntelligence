# Production First Real ERP Connector HLD

Status: **Blocked — production authority package absent; not approved for implementation.**

## Objective and scope

This design gate will authorize exactly one tenant-scoped, read-only ERP connector
after a checksum-bound production package names the vendor, product, product version,
source release/schema version and transport. The ERP remains source of truth. The
connector may extract, validate, reconcile and submit observations to existing Core
canonical services. It may not write to the ERP, trigger interventions, call AI, or
bypass Core authorization, lineage, reconciliation or outbox services.

## Required architecture

1. A closed adapter registry binds one package id/version to one transport plugin.
2. The transport runs in a separate connector network segment with an explicit
   destination allowlist; Core and AI networks cannot initiate source connections.
3. Credentials are opaque secret-manager references, injected only into the worker;
   API, database, logs, events, staging and support tools never receive secret values.
4. Extraction is bounded, read-only, checkpointed and idempotent. Checkpoints advance
   only with committed staging, canonical observations, audit and outbox records.
5. Closed versioned schemas reject drift and prohibited attributes before promotion.
6. Identity ambiguity, authority conflict, late arrivals and threshold breaches block
   automatic promotion and create safe reconciliation evidence.
7. Landing and quarantine stores are tenant-separated, encrypted, access-audited and
   deleted by approved retention schedules.
8. Core live/readiness and deterministic functions remain available during connector
   or source outages.

## Missing binding authority

`docs/pilot` contains only `mock/synthetic_reference_erp_v1`. Its manifest says
`demo-only-non-production`, forbids real connector authority, and records production
product, source, privacy and security owners as `NOT-APPROVED`. Therefore vendor,
product/version, transport, endpoints, schemas, mappings, thresholds, privacy rules,
named owners and approval dates are deliberately not populated here.

No implementation or production approval may occur until the package specified in
`PRODUCTION_FIRST_REAL_ERP_CONNECTOR_PACKAGE_REQUIREMENTS.md` exists and passes an
independent re-review.
