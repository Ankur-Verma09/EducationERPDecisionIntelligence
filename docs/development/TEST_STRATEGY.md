# Test Strategy

## Objectives

Provide evidence that business rules are correct, tenant boundaries cannot be crossed,
data transformations are traceable, integrations are replay-safe, AI outputs are
grounded, and production changes can be deployed and recovered safely.

## Test layers

- Unit: domain rules, permissions, validation, transformations, scoring, utilities.
- Component: modules with controlled database, queue, object store, and model doubles.
- Integration: migrations, repositories, connectors, identity, file ingestion,
  retrieval, notifications, and workflow transitions.
- API contract: OpenAPI conformance, validation, errors, authentication,
  authorisation, pagination, idempotency, rate limits, and correlation IDs.
- End-to-end: onboarding, ingest, risk, review, mentor assignment, intervention,
  outcome, and authorised reporting.
- Security: cross-tenant IDOR, horizontal/vertical escalation, injection, secrets,
  PII leakage, SSRF/file handling, prompt injection, retrieval isolation, write-back.
- Data quality: schema, nulls, ranges, duplicates, relationships, mapping accuracy,
  late/out-of-order data, and reprocessing.
- AI evaluation: grounded-answer rate, citation entailment, abstention, policy version,
  hallucination, leakage, injection resistance, and explanation consistency.
- Non-functional: accessibility, load/stress/soak, resilience, recovery, migration,
  backup/restore, and deletion verification.

## Tenant-isolation strategy

Maintain at least two tenants in integration fixtures. For every sensitive resource,
exercise list, get, create, update, delete, export, search, job, object-storage, cache,
and retrieval paths with valid same-tenant and invalid cross-tenant identities.
Include guessed IDs and privileged-role negative cases. Fail closed when tenant
context is absent.

## Test data

Use generated or irreversibly anonymised data only. Cover institution types, time
zones, academic calendars, boundary values, Unicode names, missing fields, duplicates,
and adversarial inputs. Never copy production credentials or raw student records.

## Automation gates

Phase 1 must define one reproducible command for format, lint, type check, unit and
integration tests. CI should add secret scanning, dependency audit, SAST, migration
checks, and an SBOM. Later gates add contract, E2E, DAST, AI evaluation, load, and
resilience suites.

Coverage is a diagnostic, not proof of quality. Initial numeric thresholds should be
set after stack selection; critical permission, tenancy, scoring, validation, and
workflow-transition logic requires branch coverage and explicit negative cases.

## Defect policy

No phase exits with a known critical security, tenant-isolation, data-corruption, or
irreversible integration defect. Flaky tests are defects and cannot be silently
retried indefinitely. Production incidents must result in a regression test when
technically feasible.

## Phase 0 result

No tests were run because the repository contained no executable project. This is
recorded as not applicable, not as a passing application test result.
