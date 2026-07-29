# Assumptions and Decisions

## Assumptions

| ID | Assumption | Reason | Validation owner/status |
|---|---|---|---|
| ASM-001 | The target is a greenfield repository | Target folder was empty | Confirmed for this assessment |
| ASM-002 | A modular monolith is the safest initial topology | Domain scope is broad; load/team boundaries unknown | Architecture approval required |
| ASM-003 | PostgreSQL is the provisional transactional store | Strong constraints, transactions, JSON, and RLS option | ADR required |
| ASM-004 | Initial risk scoring is deterministic and rule-based | Explainability and data sufficiency are mandatory | Product/data approval required |
| ASM-005 | ERP integrations are read-only until explicit write-back approval | Least privilege and ERP authority | Confirm integration policy |
| ASM-006 | Student/parent access is not in the first release | Roles are described as possible, not committed | Product decision required |
| ASM-007 | One institution is the initial tenant boundary | Terminology uses institution/tenant interchangeably | Legal/product decision required |
| ASM-008 | Raw sensitive payload retention is limited and configurable | Data minimisation requirement | Retention schedule required |
| ASM-009 | No production PII will be used for local/test environments | Security baseline | Confirm test-data policy |
| ASM-010 | Cloud, region, scale, SLOs, and budget are undecided | No deployment specification exists | Platform owner decision required |
| ASM-011 | Python 3.11/FastAPI is an acceptable reversible backend foundation | User authorised the next phase without a stack specification | Adopted for Phase 1; revisit by ADR |
| ASM-012 | GitHub Actions is the provisional CI platform | No CI platform was specified | Adopted provisionally |

## Decisions

| ID | Decision | Rationale | Status |
|---|---|---|---|
| DEC-001 | Do not implement Phase 1 during this execution | Explicit phase boundary | Accepted |
| DEC-002 | Preserve architecture choices as provisional until ADR review | Source documents are missing | Accepted |
| DEC-003 | Treat security/privacy as continuous work | Deferring controls creates systemic risk | Proposed |
| DEC-004 | Keep deterministic risk logic separate from generative AI | Reproducibility, safety, auditability | Proposed |
| DEC-005 | Separate connector read credentials from write-back credentials | Least privilege and blast-radius control | Proposed |
| DEC-006 | Prefer tenant checks in services/repositories plus database defence | Avoid reliance on a single control | Proposed |
| DEC-007 | Require idempotency and an outbox for external side effects | Safe retry and audit requirements | Proposed |
| DEC-008 | Use Python 3.11, FastAPI, SQLAlchemy, Alembic, and PostgreSQL | Typed APIs, ecosystem maturity, migrations, and Phase 0 database direction | Accepted for Phase 1 |
| DEC-009 | Use a modular-monolith package before domain/service decomposition | Avoid premature distributed complexity | Accepted for Phase 1 |
| DEC-010 | Keep the Phase 1 migration schema-empty | Tenant boundary and canonical entities belong to later approved phases | Accepted |
| DEC-011 | Liveness is process-only; readiness checks the database | Enables orchestrator-safe health semantics | Accepted |
| DEC-012 | Phase 1 cannot exit until external dependencies install and tests pass | Definition of Done forbids unvalidated completion | Accepted |
| DEC-013 | Deployed configuration fails closed on credentials, hosts, docs, database type, and TLS | Prevent development defaults reaching staging/production | Accepted |
| DEC-014 | Readiness includes the expected Alembic revision | Connectivity alone does not establish deployability | Accepted |
| DEC-015 | CI produces an SBOM and runs secret, SAST, dependency, and container scans | Phase 1 security gates require executable evidence | Accepted |
| DEC-016 | A request for the next phase cannot bypass an incomplete prior-phase gate | Protects security, correctness, and traceability requirements | Accepted |
| DEC-017 | Local Python gates do not substitute for PostgreSQL and container evidence | Database, migration, image, and runtime behavior require the actual deployment stack | Accepted |

## Conflicts

No document-to-document conflicts could be detected because no project documents
were present. One scope tension exists: the mandate asks Phase 0 to ensure the project
builds locally, but also forbids feature development before assessment. With no
selected stack or existing application, “builds locally” is not applicable yet. The
safe resolution is to make runtime selection and a reproducible skeleton the first
approved Phase 1 deliverable.

## Open questions

1. Which institution types and user journeys form the first release?
2. What is the legal tenant boundary: institution, group, campus, or another unit?
3. Which identity providers, MFA policy, and federation protocols are required?
4. What ERP vendors, schemas, volumes, sync frequency, and rate limits apply first?
5. What jurisdictions, data residency, consent, retention, and child-data rules apply?
6. Which attributes are prohibited from risk features and how is fairness approved?
7. What are the initial risk thresholds, interventions, and accountable human roles?
8. Which cloud/on-premise targets, availability zones, SLOs, RPO/RTO, and budgets apply?
9. What notification channels and write-back operations are institutionally approved?
10. What UI designs, accessibility standard, supported browsers, and export policy apply?

## Phase 1 entry-criteria disposition

The user explicitly instructed execution of the next phase, which is treated as
approval of reversible foundation defaults. Missing identity, tenant, ERP, privacy,
and deployment choices do not justify implementing those concerns early; they remain
gates for Phase 2 and production deployment.
