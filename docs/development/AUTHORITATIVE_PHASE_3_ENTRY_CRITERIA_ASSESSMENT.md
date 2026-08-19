# Superseded Connector Entry Assessment (formerly “Authoritative Phase 3”)

> **Superseded on 2026-08-05.** This document reflects an obsolete phase mapping in
> which the first ERP connector was called Phase 3. The latest local Engineering HLD
> and Implementation Backlog place connector work in authoritative Phase 2 and the
> Core Intervention Workflow in authoritative Phase 3. The current gate is
> `AUTHORITATIVE_PHASE_3_INTERVENTION_ENTRY_ASSESSMENT.md`. This file is retained as
> historical, non-authorizing evidence only.

Status: Blocked before implementation  
Date: 2026-07-30  
Authoritative phase: Phase 3 — First ERP Connector

## Objective

Deliver one read-only pilot ERP connector that maps approved source records into the
canonical education model without vendor logic entering product services. The phase
must provide identity resolution, deterministic reconciliation, explicit error and
quarantine handling, observable incremental synchronization, and auditable
completeness/freshness evidence.

The authoritative exit gate is achieved only when agreed completeness, freshness,
identity-resolution and reconciliation thresholds pass for the selected pilot
source.

## Requirements in scope

- CON-001: replaceable, versioned ERP adapter contract.
- CON-002: idempotent, retryable, observable synchronization.
- VAL-001: schema validation, reasoned rejection and quarantine.
- SYS-001: the ERP remains authoritative under the approved source matrix.
- TEN-001/TEN-002: immutable tenant ownership and cross-tenant isolation.
- DAT-001/DAT-002: canonical mapping, concrete lineage and data minimisation.
- AUD-001: immutable ingestion, reconciliation and operator audit.
- SEC-001/SEC-002: secret safety, read-only credentials and transport/input controls.
- API-001/API-002: versioned operator contracts, errors and bounded pagination.
- EVT-001/EVT-002/EVT-003: versioned events, transactional outbox and replay safety.
- OPS-001 and TST-001: freshness/lag observability and complete automated evidence.
- DOC-001: current architecture, contracts, operations and governance.

## Evidence reviewed

- Authoritative Google document
  `Education_Success_OS_Development_Plan_and_Architecture`, including integration
  architecture, Phase 3 roadmap, engineering standards and initial tickets.
- Current master plan, status, traceability, decisions and risks.
- Existing Phase 2/locally named Phase 3 HLD, LLD, canonical schemas, data model,
  privacy model, threat model, API contract and implementation plan.
- Existing source, migrations `0001`–`0006`, PostgreSQL tests and WP1 deployment
  evidence.

The existing canonical service supplies a future internal observation boundary, and
revision `0006` supplies event foundations. Existing approved documents explicitly
exclude connector transport, credentials, ingestion scheduling, landing/quarantine
and public observation ingestion.

## Entry criteria

| Criterion | Result | Required evidence |
|---|---|---|
| Design-partner/pilot institution approved | Unmet | Signed pilot charter, accountable owners and permitted domains |
| First ERP/source selected | Unmet | Product/version, environments, owner and source-system inventory |
| Read-only transport selected | Unmet | One approved API, webhook, SFTP/CSV or read-replica contract |
| Representative schema and fixtures approved | Unmet | Generated or irreversibly anonymised samples, field definitions and edge cases |
| Field-to-canonical mapping approved | Unmet | Versioned mapping for the exact first-release entity set |
| Source authority and correction policy approved | Partial | Existing generic rules plus source-specific authority registration |
| Identity-resolution policy approved | Unmet | Match keys, normalization, confidence bands, ambiguity and manual-review rules |
| Success thresholds approved | Unmet | Numeric completeness, freshness, duplicate, reject and reconciliation thresholds |
| Control totals approved | Unmet | Source/canonical counting rules and accepted exception process |
| Credential/network controls approved | Unmet | Read-only account, secret location/rotation, allowlists, TLS and egress policy |
| Landing/quarantine privacy policy approved | Unmet | Allowed fields, encryption, access, retention, deletion and raw-payload prohibition |
| Connector HLD/LLD/data model approved | Unmet | Trust boundaries, worker model, scheduling, retries, watermarks and recovery |
| Connector API/event contracts approved | Unmet | Internal ingest, operator status, quarantine and event compatibility contracts |
| Connector threat model approved | Unmet | SSRF, CSV/formula injection, archive/file abuse, replay, poisoning and tenant tests |
| Operational ownership/SLO approved | Unmet | Freshness SLO, alert owner, retry/DLQ policy and runbook |

## Entry decision

**Blocked.** Implementing now would require inventing vendor fields, identity-match
semantics, source authority, raw-data handling, credentials, transport security and
acceptance thresholds. Those choices can cause cross-tenant disclosure, silent
canonical corruption or unlawful retention. No connector code, API or migration is
authorized until the missing design package is explicitly approved.

The next phase after this one must not begin.

## Conditional implementation task list

Once entry is approved, execute these vertical work packages in order:

1. Contract and generated fixtures
   - freeze the adapter, schema-registry and mapping-version contracts;
   - add generated/irreversibly anonymised source fixtures and contract tests;
   - reject unknown entity types and prohibited attributes.
2. Additive persistence revision
   - add immutable connector registration/configuration metadata;
   - add sync run, partition/checkpoint/watermark, staging validation result,
     quarantine reason and reconciliation-control records;
   - enforce composite tenant keys, forced RLS, append-only evidence and bounded
     retention without modifying `0001`–`0006`.
3. Read-only adapter
   - implement only the approved transport behind the provider-neutral interface;
   - enforce TLS, host allowlist, timeouts, response/size limits, read-only secrets
     and bounded pagination;
   - add retry classification and cancellation.
4. Mapping and validation
   - parse the approved schema into allowlisted normalized observations;
   - apply versioned mappings and deterministic field validation;
   - quarantine failures with safe reason codes and no secret/raw-payload leakage.
5. Identity resolution and canonical ingestion
   - implement exact, normalized and ambiguous-match paths per approved policy;
   - route normalized observations through the existing canonical service;
   - preserve concrete lineage, authority, late-arrival and reconciliation behavior.
6. Incremental synchronization and events
   - persist watermarks only after the owning transaction succeeds;
   - guarantee replay safety with outbox and processed-event records;
   - test duplicate, out-of-order, partial-page, crash/restart and poison records.
7. Operator API
   - add approved connector status, run, freshness, reconciliation and quarantine
     endpoints only;
   - require explicit permissions, tenant scope, MFA/reason where sensitive,
     idempotency, ETags, opaque cursors and audit.
8. Observability and operations
   - expose safe counts, lag, freshness, reject classes and retry/DLQ state;
   - add alerts and recovery/replay/runbook procedures without source PII in logs.
9. Acceptance
   - run unit, PostgreSQL integration, API, security and two-tenant E2E suites;
   - prove migration lifecycle, RLS, secret safety, transport abuse resistance,
     reconciliation totals and numeric pilot thresholds;
   - run quality, SBOM, image, Trivy, Gitleaks, Compose and smoke gates;
   - independently review and update all governance.

## Approval inputs required

Provide and explicitly approve:

1. pilot source-system inventory and one selected first ERP;
2. generated or irreversibly anonymised representative schemas/fixtures;
3. selected read-only transport and credential/network policy;
4. exact first-release source entities and field mappings;
5. identity-resolution and manual-reconciliation rules;
6. numeric completeness, freshness, reject, duplicate and reconciliation thresholds;
7. connector HLD, LLD, data model, API/event contract, threat model and
   implementation plan.
