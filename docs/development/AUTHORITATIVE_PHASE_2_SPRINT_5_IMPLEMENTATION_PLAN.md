# Authoritative Phase 2 Sprint 5 — Demo ERP Connector Implementation Plan

Status: **Demo design independently accepted; implementation awaits separate explicit
approval.**

## Bound entry package

The replaceable package is `synthetic-reference-erp-v1@1.0.0`, vendor/product
`Example Education Systems / Synthetic Reference ERP 1.0`, transport
`in-process-read-only-csv-test-double`. It includes generated schemas, mappings,
authority and identity rules, privacy lifecycle, deterministic thresholds and a
demo sponsor approval. All production owner approvals remain `NOT-APPROVED`.

## Planned vertical work packages after explicit approval

1. Freeze package checksums, registry enum and generated fixture provenance.
2. Add the in-process read-only adapter and no-network/no-credential negatives.
3. Add self-contained additive migration `0008`; never edit `0001`–`0007`.
4. Persist schema/mapping/authority/identity/threshold snapshots under forced RLS.
5. Implement bounded checkpointed extraction, validation and canonical projection.
6. Implement ambiguity, drift, quarantine, retention and rights cleanup behavior.
7. Implement deterministic threshold reconciliation and safe versioned events.
8. Add closed operator APIs and OpenAPI/idempotency/ETag/MFA tests.
9. Automate C5-T01–C5-T24, including PostgreSQL kill/resume and tenant isolation.
10. Run quality, unit, PostgreSQL, migration lifecycle, image, SBOM, Trivy,
    Gitleaks, Core live/readiness and adapter-outage smoke gates.
11. Update governance and conduct an independent completion review.

## Demo definition of done

All generated source fields are mapped or rejected; no external path, socket,
credential or real person data is accepted; tenant isolation, append-only evidence,
checkpoint recovery, thresholds, cleanup and Core isolation are proven; all gates
pass; and an independent reviewer accepts completion. This definition never grants
production readiness. Intervention workflows and Phase 4 AI remain prohibited.
