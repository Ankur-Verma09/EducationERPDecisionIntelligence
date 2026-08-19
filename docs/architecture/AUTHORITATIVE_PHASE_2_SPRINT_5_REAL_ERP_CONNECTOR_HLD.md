# Authoritative Phase 2 Sprint 5 — Demo ERP Connector HLD

Status: **Approved for generated demo-only design; not production or implementation approval.**

## Objective and boundary

Sprint 5 demo delivers one read-only connector for `Example Education Systems /
Synthetic Reference ERP / 1.0`, package `synthetic-reference-erp-v1@1.0.0`, through
an in-process read-only CSV test double. It reuses Sprint 4 jobs, mappings, canonical
observation/lineage, reconciliation, outbox, tenancy and Core/AI isolation.

All records are generated. No socket, external ERP, credential, uploaded file,
intervention workflow, write-back or AI service is enabled. The package is approved
only for local/demo use and is never production authority.

## Bound demo profile

The checksum-controlled folder `docs/pilot/mock/synthetic_reference_erp_v1` defines
six source objects, eight valid records, nine negative scenarios and all-nine
canonical mappings. Authority is mock-primary from 2030-01-01. Identity is exact on
tenant + source system + stable source key; automatic learner merge is forbidden.
Landing retention is 24 hours and quarantine retention is 7 days.

Demo gates are completeness 100%, freshness <=60 minutes, rejection <=5%, duplicate
<=2%, unresolved reconciliation 0 and unexplained count variance 0. Any breach
blocks demo promotion. These values cannot become production defaults.

## Components and trust boundaries

1. Closed registry enables `synthetic_reference_erp_v1` only.
2. In-process transport exposes `read_snapshot` and `read_page`; egress is disabled.
3. Connector configuration accepts package id/version, scenario and explicit test
   clock only. It accepts no URL, path, query, upload or credential.
4. Manifest and schema fingerprints are verified before reading a record.
5. Closed mapping uses copy, typed parse, enum map, reference and ISO-date transforms.
6. Ambiguous identity reconciles and never auto-merges.
7. Every canonical change traverses `record_observation` and authority/temporal rules.
8. Threshold reconciliation and safe events expose counts/codes only.

## Availability and approval gates

Timeout, throttling, schema drift, invalid credential simulation or threshold breach
remains connector-domain state; Core live/readiness remains healthy. Checkpoints
advance atomically with committed outcomes.

Independent acceptance of this concrete design is required before implementation.
Implementation then requires a separate explicit user instruction. Production stays
blocked until a real, owner-approved package replaces every mock value.
