# Master Development Plan

## Document control

- Status: Authoritative Phase 2 canonical/integration work is accepted for generated
  scope. Authoritative Phase 3 Core Intervention Workflow design is independently
  accepted; implementation awaits separate explicit user approval and has not
  started. A real ERP remains blocked for pilot/production. Phase 4 has not started.
- Updated: 2026-08-05
- Authority: supplied project mandate; no product or design source documents were present
- Change rule: material scope, security, tenancy, or data-governance decisions require an ADR

## System understanding

The product is a multi-tenant decision-intelligence layer for schools, colleges, and
universities. It ingests authorised ERP data through replaceable adapters, maps it to
a canonical education model, produces explainable risk insights, and supports
human-controlled interventions. The ERP remains authoritative. AI may explain,
summarise, retrieve approved policy, and draft recommendations; it may not determine
access, invent institutional facts, or perform consequential actions autonomously.

Primary users include institutional leadership, registrars, department leaders,
faculty, mentors, admissions and finance teams, ERP/IT administrators, and platform
administrators. Student and parent access is possible but not yet confirmed.

## Repository assessment

At assessment time the target directory was new and empty. It contained:

- no source code, language, framework, package manager, build tool, or conventions;
- no PRD, proposal, HLD, LLD, API specification, database design, UI design, workflow,
  AI/ML specification, compliance profile, or testing strategy;
- no environment files, tests, CI/CD, containers, migrations, or infrastructure;
- no existing components to classify as complete or partial.

Consequently, this plan establishes a safe baseline but does not claim that product
requirements or architecture have been approved.

## Requirements summary

### Business objective

Turn authorised ERP data into timely, explainable institutional insights and
auditable interventions without replacing or weakening the ERP.

### Major modules

Tenant and identity management; connector framework; canonical data model; validation
and quarantine; risk/rule engine; knowledge and AI explanation layer; intervention
workflow; dashboards/reporting; notifications/write-back; audit/security;
observability and operations.

### Non-functional requirements

Secure multi-tenancy, least privilege, traceability, explainability, configurable
institution rules, idempotent integrations, reliable processing, accessibility,
scalability, observability, recovery, and production-grade automated testing.

### Data and integration requirements

Ingest CSV/Excel, REST, webhooks, and read-only databases; preserve source identifiers
and lineage; version schemas and mappings; quarantine invalid data; minimise PII;
separate read from write credentials; make write-back confirmed, restricted,
idempotent, and audited.

### AI/ML requirements

Start with reproducible deterministic rules. Introduce ML only after data sufficiency,
fairness, legal, and evaluation gates. Ground generative answers in authorised,
versioned sources with citations. Record model, prompt/rule version, inputs, evidence,
and generation time. Test hallucination, leakage, injection, and explanation fidelity.

### Deployment and testing requirements

Deployment topology is not specified. The baseline expects containerised local
development, automated build/lint/test/security checks, migration safety, staged
promotion, rollback, backups, monitoring, and runbooks. Testing spans unit,
integration, API, end-to-end, tenant isolation, security, data quality, AI evaluation,
performance, and resilience.

## Provisional architecture principles

1. Begin as a modular monolith with explicit domain boundaries and asynchronous job
   workers. Split services only from measured scaling, isolation, or ownership needs.
2. Use PostgreSQL with enforced tenant ownership; evaluate PostgreSQL row-level
   security as defence in depth, not as the only authorisation control.
3. Use an outbox/idempotency pattern for jobs and external effects.
4. Keep raw landing/quarantine data separated from validated canonical records.
5. Route all LLM and retrieval access through application services with the same
   tenant and role checks as other data access.
6. Store immutable audit events for sensitive actions and access.
7. Treat technology selections as ADR candidates until source documents are received.

## Recommended phases and gates

| Phase | Name | Principal exit gate |
|---|---|---|
| 0 | Discovery and baseline | Assessment and planning documents reviewed |
| 1 | Project foundation | Local stack, CI, health, logging, errors, migrations pass |
| 2 | Identity and multi-tenancy | AuthZ and cross-tenant negative tests pass |
| 3 | Canonical education model | Constraints, lineage, tenancy, migrations pass |
| 4 | ERP connector framework | Mock/CSV ingestion is idempotent and observable |
| 5 | Validation and transformation | Invalid data is explained and quarantined |
| 6 | Explainable risk engine | Scores reproduce and evidence matches explanations |
| 7 | AI knowledge and explanation | Grounding, citations, injection/leakage tests pass |
| 8 | Intervention workflow | Ownership, approvals, transitions, and audit pass |
| 9 | Role-based dashboards | Backend permissions and workflow E2E tests pass |
| 10 | Notifications and write-back | Confirmation, idempotency, audit, retries pass |
| 11 | Security/privacy hardening | No unresolved critical finding |
| 12 | Reliability/performance | SLO and recovery tests meet agreed targets |
| 13 | Deployment/readiness | Staging, migration, rollback, and ownership approved |

Security and privacy work is continuous; Phase 11 is a formal hardening gate, not the
first time security is addressed.

## Phase 1 proposed task breakdown

1. Obtain/approve PRD, architecture constraints, deployment target, compliance
   profile, tenancy model, and supported identity providers.
2. Record ADRs for backend/frontend stack, database, async jobs, identity, API style,
   repository layout, and test tooling.
3. Scaffold bounded modules without implementing product workflows.
4. Add typed configuration with fail-fast validation and a secret-free
   `.env.example`.
5. Add structured JSON logging, correlation IDs, safe redaction, and global errors.
6. Add `/api/v1/health/live` and `/api/v1/health/ready`.
7. Configure PostgreSQL migrations and containerised local dependencies.
8. Add OpenAPI generation, format/lint/type-check/test commands, and coverage gates.
9. Add CI for build, tests, secret scanning, dependency audit, and static analysis.
10. Add foundation unit/integration/API tests and update traceability/status records.

## Authoritative roadmap clarification — 2026-08-05

The latest local Education Success OS Engineering HLD and Implementation Backlog
supersede the provisional phase table above for sequencing. Authoritative Phase 2
contains canonical data and integration: Sprint 4 is the integration framework with
a generated mock ERP adapter, and Sprint 5 is the first real ERP connector.
Authoritative Phase 3 is the core intervention workflow; authoritative Phase 4 is
the self-hosted knowledge/AI layer.

The next executable unit is therefore **Phase 2 Sprint 4 — Integration Framework
and Generated Mock Connector**. Its design package is independently reviewed but
awaits explicit implementation approval. Sprint 5 remains blocked by the missing
pilot ERP package. Phase 3 and Phase 4 have not started.

## Phase 1 entry criteria

- Product owner accepts or amends Phase 0 assumptions.
- Deployment and data-residency constraints are known.
- Authentication/identity direction is known.
- Minimum supported ERP ingestion path is prioritised.
- Initial tenant definition and isolation policy are approved.
- Development runtime and CI platform are approved.

Until these are met, scaffolding choices would be speculative and may create a
fundamentally incompatible architecture.

## Phase 1 execution note

The user authorised Phase 1 on 2026-07-28. Provider-neutral, reversible foundation
defaults were adopted, while identity, tenant, ERP, and product choices were kept out
of scope. Implementation exists, but the phase exit gate is not met until dependency
installation, lint, type checking, migrations, automated tests, and the container
build complete successfully.

## Independent-review remediation note

The Phase 1 review findings were addressed in source, tests, containers, and CI:
production settings fail closed, logs sanitize message/exception secrets, readiness
is migration-aware, Compose migrates before startup, PostgreSQL integration and error
paths are covered, and security/SBOM/image gates are configured. Phase 1 remains open
until the dependency registry and Docker daemon are available and all gates pass.

## Phase 1 acceptance note — 2026-07-29

All requested Phase 1 executable gates passed after remediation: dependency
consistency and audit, fully hashed lock, Ruff, strict mypy, Bandit, 32 PostgreSQL-
enabled tests with 95.18% coverage, Alembic upgrade/downgrade/upgrade, image build,
zero-critical Trivy scan, migration-first Compose startup, and live/ready container
smoke tests. Phase 1 is locally accepted. A successful remote CI run remains
recommended branch-governance evidence.

## Current authoritative execution position — 2026-08-05

Sprint 4 is accepted. Sprint 5 now has an independently accepted generated demo-only
connector using `synthetic-reference-erp-v1@1.0.0`; it is not a real ERP connector
and grants no production readiness. A real ERP connector remains blocked by owner-approved source,
transport, credential, privacy and threshold inputs. Authoritative Phase 3
interventions and Phase 4 AI services have not started.

### Phase 3 sequencing reassessment

The authoritative Phase 2 exit language permits a first ERP connector **or mock connector**. The accepted generated connectors satisfy Phase 3 sequencing without granting production readiness. The Authoritative Phase 3 Core Intervention Workflow design package is independently accepted. The next authorized gate is separate explicit user approval for implementation. The missing real ERP remains a parallel blocker for real-pilot and production validation. Phase 4 remains prohibited.

### Phase 3 independently accepted design

The intervention HLD, LLD, data model, API/event contract, threat model, implementation plan and entry reassessment are independently accepted after remediation. The package is deterministic, human-owned, generated-data-only and independent of AI availability. Implementation remains prohibited pending separate explicit user approval.
