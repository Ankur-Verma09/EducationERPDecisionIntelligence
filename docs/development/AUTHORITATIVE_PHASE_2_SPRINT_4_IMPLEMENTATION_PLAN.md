# Authoritative Phase 2 Sprint 4 Implementation Plan

Status: Awaiting explicit design approval. No implementation may start from this document alone.

## Entry criteria

Met: canonical entity/privacy/authority services accepted; Work Package 1 event/outbox foundation accepted; generated-only data rule; Core/AI isolation; additive migration discipline. Explicit approval of this design package remains outstanding. Real ERP inputs are not required because all real transports are disabled.

## Vertical work packages

1. Add connector contracts, generated fixture schemas and adapter registry with unit/security tests.
2. Add self-contained revision `0007`, models, RLS/immutability grants and migration lifecycle/catalog tests.
3. Add mapping/validation/quarantine services and generated valid/invalid/duplicate/late scenarios.
4. Add durable job, lease, batch, watermark and restart-safe worker execution through canonical services.
5. Add reconciliation and safe lifecycle outbox events.
6. Add authorized APIs, persistent idempotency, ETags, opaque cursors, MFA/reason replay and OpenAPI tests.
7. Complete C4-T01-C4-T24 traceability with unit, PostgreSQL, API, security and E2E execution.
8. Run Ruff format/lint, strict mypy, Bandit, dependency consistency/audit, full PostgreSQL suite with coverage gate, `0007` migration lifecycle, image builds, SBOM validation, Trivy, Gitleaks, Core-only and connector smoke/resilience gates.
9. Update API docs, status, traceability, decisions and risks; perform an independent completion review.

## Definition of done

All HLD exit criteria and threat cases pass with no skips; tenant isolation is tested through the non-superuser `NOBYPASSRLS` runtime role; revisions `0001`-`0006` are byte-unchanged; documentation matches executable contracts; no critical scan finding exists. Sprint 4 may then be accepted, but Sprint 5 remains blocked pending the real pilot package.

## Explicit exclusions

No ERP product/version choice, external transport, credential use, uploaded customer data, intervention workflow, notification/write-back, broker deployment, retrieval, model routing, embeddings, inference or other Phase 4 AI service.

