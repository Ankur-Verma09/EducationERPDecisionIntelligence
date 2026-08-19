# Requirements Traceability Matrix

Status values: `Identified`, `Planned`, `In progress`, `Implemented`, `Verified`,
`Deferred`, `Blocked`. No feature is complete until implementation and tests exist.

The latest local Education Success OS Engineering HLD and Implementation Backlog
control phase numbering. Existing canonical education and generated connector work
is credited to authoritative Phase 2. Authoritative Phase 3 is the Core Intervention
Workflow and is authorized for design only; Phase 4 is the self-hosted AI layer.

| Requirement ID | Source document | Requirement | Module | Phase | Implementation file | Test file | Status |
|---|---|---|---|---|---|---|---|
| SYS-001 | Supplied mandate | ERP remains system of record | Architecture | All | TBD | TBD | Planned |
| TEN-001 | Supplied mandate | Every business record has tenant ownership | Platform/Data | 2-3 | TBD | TBD | Planned |
| TEN-002 | Supplied mandate | Prevent cross-tenant access server-side | Identity/Data | 2 | TBD | TBD | Planned |
| IAM-001 | Supplied mandate | Roles and permissions constrain APIs | Identity | 2 | TBD | TBD | Planned |
| AUD-001 | Supplied mandate | Audit sensitive access and mutations | Audit | 1-13 | TBD | TBD | Planned |
| API-001 | Supplied mandate | Versioned APIs with consistent validation/errors | API | 1 | src/education_erp/main.py; src/education_erp/errors.py | tests/api/test_health.py | Implemented; verification blocked |
| API-002 | Supplied mandate | Pagination and correlation IDs | API | 1 | src/education_erp/middleware.py | tests/security/test_http_baseline.py | Partially implemented; pagination deferred until collections |
| DAT-001 | Supplied mandate | Canonical education data model with lineage | Data | 3 | TBD | TBD | Planned |
| DAT-002 | Supplied mandate | Minimise unnecessary sensitive data | Data/Security | 3,11 | TBD | TBD | Planned |
| CON-001 | Supplied mandate | Replaceable ERP connector contract | Integration | 4 | TBD | TBD | Planned |
| CON-002 | Supplied mandate | Idempotent, retryable, observable sync | Integration | 4 | TBD | TBD | Planned |
| VAL-001 | Supplied mandate | Validate and quarantine rejected records with reasons | Data Quality | 5 | TBD | TBD | Planned |
| RSK-001 | Supplied mandate | Reproducible explainable risk scoring | Risk | 6 | TBD | TBD | Planned |
| RSK-002 | Supplied mandate | Preserve factors, evidence, confidence, and version | Risk | 6 | TBD | TBD | Planned |
| RSK-003 | Supplied mandate | Human override for risk outputs | Risk | 6 | TBD | TBD | Planned |
| AI-001 | Supplied mandate | Ground policy answers in authorised sources | AI | 7 | TBD | TBD | Planned |
| AI-002 | Supplied mandate | AI cannot calculate authoritative records or bypass access | AI/Security | 7 | TBD | TBD | Planned |
| AI-003 | Supplied mandate | Test hallucination, leakage, injection, citations | AI QA | 7 | TBD | TBD | Planned |
| INT-001 | Authoritative Engineering HLD/Backlog | Human-owned, auditable intervention workflow | Workflow | 3 | `src/education_erp/interventions/` (planned) | Phase 3 suites (planned) | Designed; implementation not started |
| UI-001 | Supplied mandate | Role-limited, accessible decision dashboards | UI/API | 9 | TBD | TBD | Planned |
| NTF-001 | Supplied mandate | Traceable and deduplicated notifications | Notification | 10 | TBD | TBD | Planned |
| WBK-001 | Supplied mandate | Confirmed, restricted, audited ERP write-back | Integration | 10 | TBD | TBD | Planned |
| SEC-001 | Supplied mandate | No secrets in source or logs | Security | All | src/education_erp/logging.py; .env.example; .gitignore | tests/unit/test_logging.py | Remediated; direct probe passed; full verification blocked |
| SEC-002 | Supplied mandate | Encryption, least privilege, masking, retention/deletion | Security | 1-11 | TBD | TBD | Planned |
| OPS-001 | Supplied mandate | Metrics, traces, logs, alerts, resilience | Operations | 1,12 | src/education_erp/logging.py; src/education_erp/api/health.py | tests/api/test_health.py | Phase 1 portion implemented; verification blocked |
| OPS-002 | Supplied mandate | Backup, restore, migration, rollback procedures | Operations | 11-13 | TBD | TBD | Planned |
| TST-001 | Supplied mandate | Automated tests appropriate to every phase | Quality | All | pyproject.toml; .github/workflows/ci.yml | tests/ | Implemented; execution blocked |
| DOC-001 | Supplied mandate | Keep plans, status, decisions, risks, and traceability current | Governance | All | docs/development/*; docs/api/* | N/A | Verified |
| FND-001 | Phase 1 plan | Typed, fail-fast environment configuration | Foundation | 1 | src/education_erp/config.py; .env.example | tests/unit/test_config.py | Hardened; verification blocked |
| FND-002 | Phase 1 plan | Liveness and migration-aware database readiness endpoints | Foundation API | 1 | src/education_erp/api/health.py; src/education_erp/database.py | tests/api/test_health.py; tests/e2e/test_foundation_journey.py | Hardened; verification blocked |
| FND-003 | Phase 1 plan | PostgreSQL migrations and containerised local development | Foundation Data | 1 | migrations/; alembic.ini; compose.yaml | tests/integration/test_database.py | PostgreSQL tests/migration job added; runtime verification blocked |
| FND-004 | Phase 1 plan | Global build, lint, type, test, security-scan, SBOM, and CI tooling | Foundation Quality | 1 | pyproject.toml; Makefile; .github/workflows/ci.yml | tests/ | Hardened; execution blocked |
| FND-005 | Phase 1 plan | Secure baseline HTTP headers and trusted hosts | Foundation Security | 1 | src/education_erp/main.py; src/education_erp/middleware.py | tests/security/test_http_baseline.py; tests/api/test_errors.py | Expanded; verification blocked |
| FND-006 | Authoritative Engineering HLD | Separate Core/AI profiles, networks and bounded resources | Platform Isolation | 1 | compose.yaml | tests/security/test_compose_isolation.py; tests/api/test_ai_contract_isolation.py | Verified |
| FND-007 | Authoritative Engineering HLD | Internal provider-neutral AI boundary with no Core DB credentials | Platform Isolation | 1 | src/education_erp/ai_contracts.py; src/education_erp/ai_test_double.py; compose.yaml | tests/api/test_ai_contract_isolation.py; tests/security/test_compose_isolation.py | Verified |
| EVT-001 | Authoritative LLD | Versioned event envelope | Contracts | 1-2 | src/education_erp/events.py | tests/unit/test_event_foundation.py | Verified |
| EVT-002 | Authoritative LLD | Transactional outbox in owning transaction | Events | 1-2 | src/education_erp/persistence/event_models.py; migrations/versions/0006_event_foundation.py | tests/unit/test_event_foundation.py; tests/integration/test_event_postgresql.py | Verified |
| EVT-003 | Authoritative LLD | Consumers persist processed event IDs and tolerate replay | Events | 1-2 | src/education_erp/events.py; src/education_erp/persistence/event_models.py | tests/unit/test_event_foundation.py; tests/integration/test_event_postgresql.py | Verified |

This is a mandate-level seed matrix. It must be decomposed into testable product
requirements when the PRD, API, workflow, security, and design documents arrive.

Revalidation on 2026-07-28 confirmed that FND-001 through FND-005 cannot advance to
`Verified`: dependency installation and Docker/PostgreSQL execution remain blocked.
No Phase 2 requirement status was changed.

## Phase 1 executable revalidation — 2026-07-29

| Requirement | Updated verification status |
|---|---|
| API-001 | Verified locally by API/error tests; deployed-container verification blocked |
| API-002 | Correlation-ID portion verified locally; pagination remains deferred until collection APIs exist |
| SEC-001 | Verified locally by message, exception, bearer-token, DSN, and error-path redaction tests |
| OPS-001 | Health/logging portion verified locally; real PostgreSQL/deployed readiness blocked |
| TST-001 | Local suite verified: 30 passed, 1 PostgreSQL test skipped; remote CI blocked |
| FND-001 | Verified locally by configuration tests and strict mypy |
| FND-002 | Verified with SQLite component/E2E tests; PostgreSQL readiness blocked |
| FND-003 | Implemented but not verified; PostgreSQL migration lifecycle is blocked |
| FND-004 | Ruff, mypy, Bandit, pip-audit, coverage, hashed lock, and SBOM verified locally; image scan and remote CI blocked |
| FND-005 | Verified locally across success and error responses |

The phase-level status remains **Blocked**, not complete, because FND-003 and the
container portions of FND-004 have mandatory unexecuted gates. No Phase 2 status was
advanced.

## Final Phase 1 traceability update — 2026-07-29

| Requirement | Final status/evidence |
|---|---|
| API-001 | Verified by API/error tests and deployed container smoke test |
| API-002 | Correlation-ID portion verified; pagination remains tied to future collection APIs |
| SEC-001 | Verified by redaction tests, Bandit, pip-audit, and zero-critical image scan |
| OPS-001 | Phase 1 health/logging portion verified against PostgreSQL and the container |
| TST-001 | Verified locally: 32 tests, no skips, 95.18% coverage |
| FND-001 | Verified, including real environment-source parsing |
| FND-002 | Verified against PostgreSQL and the container |
| FND-003 | Verified by migration lifecycle, migration job, PostgreSQL test, and Compose startup/shutdown |
| FND-004 | Verified locally by quality, security, SBOM, image, and smoke gates |
| FND-005 | Verified across normal and error responses |

Phase 1 foundation requirements are verified. No Phase 2 status was advanced.

## Phase 2 entry assessment — 2026-07-29

TEN-001, TEN-002, IAM-001, and the Phase 2 portion of AUD-001 remain **Blocked**.
Their implementation and test design depend on an approved tenant hierarchy,
identity trust model, permission matrix, privacy baseline, and threat model. No
implementation or test file is claimed while those inputs remain unresolved.

## Phase 2 design approval update — 2026-07-29

TEN-001, TEN-002, IAM-001, and the Phase 2 portion of AUD-001 advance from `Blocked`
to `Planned`. Their approved design sources are the Phase 2 security model, HLD, LLD,
data model, threat model, API contract and implementation plan. They do not advance
to `Implemented` until code, migrations and the complete test matrix exist and pass.

## Phase 2 implementation update — 2026-07-29

- TEN-001: `In progress` — tenant ownership models, composite constraints and RLS
  migration exist; PostgreSQL execution evidence is pending.
- TEN-002: `In progress` — tenant context, safe `404`, application negative tests and
  PostgreSQL RLS test exist; PostgreSQL test is pending execution.
- IAM-001: `In progress` — OIDC verifier, memberships and built-in RBAC protect the
  implemented endpoints; the approved endpoint/permission matrix is incomplete.
- AUD-001: `In progress` — onboarding, membership and role assignment audit events
  are atomic and immutable; remaining sensitive operations are not implemented.

## Phase 2 PostgreSQL traceability update — 2026-07-29

- TEN-001: `In progress` — Phase 2 tenant tables have explicit ownership and
  PostgreSQL composite constraints; approved endpoint scope remains incomplete.
- TEN-002: `In progress` — forced RLS is verified under a non-superuser,
  non-`BYPASSRLS` runtime identity, including tenant switching and pool reuse.
- IAM-001: `In progress` — the implemented OIDC/RBAC subset passes, but lifecycle,
  scoped delegation, support access, and the complete permission matrix remain.
- AUD-001: `In progress` — immutable atomic events pass for implemented mutations;
  unimplemented sensitive operations and audit-access auditing remain.
- TST-001: `In progress` — PostgreSQL-enabled suite passes 48 tests at 90.97%;
  Phase 2 image/scan/smoke and missing-feature tests remain.

### Blocker-remediation evidence

- TEN-001/TEN-002 remain `In progress`: migration `0003`, hierarchy lifecycle,
  tenant suspension denial, and the full PostgreSQL cycle pass; new tenant-table RLS
  policies still require explicit cross-tenant tests.
- IAM-001 remains `In progress`: membership lifecycle, last-owner checks, role
  revocation, expired-assignment exclusion and support approvals are tested; scoped
  delegation coverage is incomplete.
- TST-001 remains `In progress`: 50 tests pass at 90.15%; Docker and remaining
  contract-negative gates are not complete.

## Phase 2 final remediation traceability — 2026-07-29

- TEN-001/TEN-002: `Verified` — tenant ownership, composite constraints, forced RLS,
  hidden lookups, pooled isolation and cross-tenant/scope tests pass.
- IAM-001: `Verified` — OIDC, membership, RBAC, MFA, lifecycle, last-owner and
  scoped-delegation controls pass.
- AUD-001 (Phase 2): `Verified` — mutations and audit access create immutable events.
- API-002 (Phase 2): `Verified` — bounded opaque cursors and request IDs pass.
- SEC-002 (Phase 2): `Verified` — least-privilege runtime identity, RLS, security
  epochs, support expiry/revocation and deletion-request controls pass.
- TST-001 (Phase 2): `Verified` — 54 PostgreSQL tests, no skips, 90.06% coverage;
  migration, image, Trivy, secret and smoke gates pass.
- DOC-001: `Verified` — final status, review, API, decisions and risks are current.

### Semantic contract audit addendum

- API-001/API-002: `Verified` — OpenAPI documents `Idempotency-Key` for every
  mutation and `If-Match` for optimistic role revocation.
- IAM-001/SEC-002: `Verified` — deletion requests verify an active tenant-owner role
  assignment; invalid approval returns `403`.
- TST-001: `Verified` — 55 PostgreSQL tests, no skips, 90.16% coverage; existing
  `0003 -> 0004` and full `0004 -> base -> 0004` migration paths pass.

### PostgreSQL API-runtime parity addendum

- TEN-002/IAM-001: `Verified` — platform onboarding and lifecycle APIs pass through
  the real non-`BYPASSRLS` runtime identity with transaction-local tenant context.
- TST-001: `Verified` — 56 PostgreSQL tests, no skips, 90.32% coverage.

## Phase 2 persistent-replay process-boundary addendum — 2026-07-29

- API-002: `Verified` — an idempotent mutation replayed from a newly constructed
  API instance returns the persisted original response.
- TEN-001: `Verified` — the cross-instance replay runs through the
  `NOSUPERUSER NOBYPASSRLS` application role with tenant context enforced.
- TST-001: `Verified` — PostgreSQL verification asserts exactly one business row
  after the original request and cross-instance replay; the full result remains
  56 passed, no skips, 90.32% coverage.

All quality, migration, SBOM, image, vulnerability, secret, container-health and
smoke gates were rerun successfully. Phase 3 has not started.
- OPS-001: `Verified` — CI and Makefile use CycloneDX `--outfile` and produce a
  validated 91-component SBOM.

## Phase 3 entry assessment — 2026-07-29

- SYS-001: `Blocked` — ERP authority, reconciliation, correction, and source
  precedence rules are not approved.
- TEN-001/TEN-002: `Blocked` for Phase 3 — canonical tenant ownership is required,
  but education-record authorization and relationship scopes are not designed.
- DAT-001: `Blocked` — canonical entities, identifiers, temporal semantics, merge
  rules, and lineage model are not approved.
- DAT-002/SEC-002: `Blocked` for Phase 3 — student/child-data classification,
  purpose, minimisation, masking, retention, deletion, and subject-rights rules are
  unresolved.
- AUD-001/API-001/API-002: `Blocked` for Phase 3 — sensitive-access audit policy and
  API contract do not exist.
- TST-001: `Planned` — the global strategy exists, but Phase 3 invariants, generated
  fixtures, security matrix, and populated-migration scenarios depend on the missing
  designs.
- DOC-001: `Verified` — the blocked entry decision and conditional task list are
  recorded in `PHASE_3_ENTRY_CRITERIA_ASSESSMENT.md`.

No Phase 3 implementation or verification file is claimed.

### Phase 3 design approval update — 2026-07-29

- SYS-001: `Planned` — the approved authority policy keeps the ERP authoritative per
  tenant/entity type and prevents recency-only overwrite.
- TEN-001/TEN-002: `Planned` for Phase 3 — immutable tenant ownership, composite
  tenant keys, application scope checks, hidden lookups, and forced RLS are specified.
- DAT-001: `Planned` — the approved glossary, generated schemas, stable identifiers,
  effective dating, immutable observations, concrete lineage requirement,
  supersession, and reconciliation define the canonical model.
- DAT-002: `Planned` — the first release is minimised; prohibited fields, raw
  payloads, arbitrary extensions, and production examples are excluded.
- AUD-001: `Planned` for Phase 3 — sensitive reads, mutations, identifier reveal,
  lineage, reconciliation, export metadata, and subject-rights operations require
  minimised audit.
- API-001/API-002: `Planned` for Phase 3 — versioned routes, strict schemas, standard
  errors, persistent idempotency, ETags, opaque bound cursors, and request IDs are
  contractually defined.
- SEC-002: `Planned` for Phase 3 — permission/scope matrix, MFA/reason, masking,
  processing restriction, retention metadata, deletion eligibility, and subject
  rights are approved.
- TST-001: `Planned` — all 26 threat cases and unit, PostgreSQL, API, security, E2E,
  migration, image, scan, and smoke gates are defined.
- DOC-001: `Verified` — the Phase 3 design, approval, independent review, entry
  reassessment, decisions, risks, and traceability are current.

Approved design/plan files:

- `docs/architecture/PHASE_3_SECURITY_PRIVACY_MODEL.md`
- `docs/architecture/PHASE_3_CANONICAL_SCHEMAS.md`
- `docs/architecture/PHASE_3_HLD.md`
- `docs/architecture/PHASE_3_LLD.md`
- `docs/architecture/PHASE_3_DATA_MODEL.md`
- `docs/security/PHASE_3_THREAT_MODEL.md`
- `docs/api/PHASE_3_API_CONTRACT.md`
- `docs/development/PHASE_3_IMPLEMENTATION_PLAN.md`
- `docs/development/PHASE_3_INDEPENDENT_REVIEW.md`
- `docs/development/PHASE_3_ENTRY_CRITERIA_ASSESSMENT.md`

Phase 3 requirements remain `Planned`, not `Implemented`, until code and executable
evidence exist. Phase 4 has not started.

### Authoritative Work Package 1 acceptance — 2026-07-30

- FND-006/FND-007: `Verified` — separate bounded Core/AI profiles and networks,
  credential-free AI test-double operation, and AI-outage isolation pass.
- EVT-002/EVT-003: `Verified` — versioned provider-neutral envelopes,
  transactional outbox and processed-event replay foundations pass unit and real
  PostgreSQL tests under additive revision `0006`.
- TST-001: `Verified for Work Package 1` — 97 PostgreSQL-backed tests, no skips,
  90.91% coverage, migration lifecycle, image, Trivy, Gitleaks and smoke gates pass.

These statuses apply only to Work Package 1 foundations. ERP connectors and the
remaining authoritative Phase 2 synchronization scope are not implemented;
authoritative Phase 3 and Phase 4 remain unimplemented.

### Authoritative Phase 3 entry assessment — 2026-07-30

- CON-001, CON-002 and VAL-001: `Blocked` — the first ERP, transport, representative
  source schema, mapping and quarantine contract are not approved.
- SYS-001 and DAT-001: `Blocked for connector scope` — generic authority/lineage
  exists, but source-specific authority, identity matching and control totals do not.
- TEN-001, TEN-002, AUD-001, SEC-001 and SEC-002: `Planned for connector scope` —
  existing controls are prerequisites; connector transport, secrets, staging and
  quarantine require an approved threat model and executable negatives.
- EVT-001, EVT-002 and EVT-003: `Verified foundation` — revision `0006` is available
  but does not itself implement ingestion or relay workers.
- TST-001 and DOC-001: `In progress` — the blocked entry assessment and conditional
  task list are current; no connector implementation tests can be claimed.

Source: `AUTHORITATIVE_PHASE_3_ENTRY_CRITERIA_ASSESSMENT.md`. No later phase has
started.

### Authoritative Phase 2 Sprint 4 design traceability — 2026-08-05

- CON-001: `Designed, approval pending` — provider-neutral adapter boundary with
  only generated `generated_mock_v1` enabled; no external transport or credential.
- CON-002: `Designed, approval pending` — durable jobs, leases, batches, watermarks,
  replay and reconciliation are specified for additive revision `0007`.
- VAL-001: `Designed, approval pending` — closed schemas, declarative mappings,
  per-record safe quarantine and generated valid/invalid/duplicate/late fixtures.
- SYS-001/DAT-001: `Verified prerequisite` — accepted canonical observation,
  authority, lineage and temporal services are the sole projection boundary.
- TEN-001/TEN-002/AUD-001/SEC-001/SEC-002: `Designed for Sprint 4` — forced RLS,
  composite tenant keys, permission/scope/MFA/reason, safe audit and retention.
- EVT-001/EVT-002/EVT-003: `Verified foundation; Sprint 4 extension designed` —
  connector lifecycle events use the existing version-1 envelope and outbox.
- TST-001: `Planned` — C4-T01-C4-T24 plus unit, PostgreSQL, API, security, E2E,
  migration, quality, image, scan and smoke gates are mandatory.
- DOC-001: `Verified for design` — the complete Sprint 4 design package and review
  are current; implementation remains unapproved.

Sprint 5 real-source requirements remain blocked by the pilot package. Phase 3 and
Phase 4 have not started.

### Authoritative Phase 2 Sprint 4 implementation acceptance candidate — 2026-08-05

- CON-001: `Verified for Sprint 4` — closed generated adapter registry, generated
  scenarios and canonical-service boundary pass API/unit/E2E tests.
- CON-002: `Verified for Sprint 4` — jobs, leases, batches, watermarks, restart-safe
  replay and reconciliation persist under revision `0007`.
- VAL-001: `Verified for Sprint 4` — strict validation, prohibited-field rejection,
  value-free quarantine and valid/invalid/duplicate/late manifests pass.
- TEN-001/TEN-002: `Verified` — all ten connector tables force RLS; non-superuser,
  non-`BYPASSRLS` PostgreSQL negatives pass.
- AUD-001/SEC-001/SEC-002: `Verified for Sprint 4` — permissions, hidden tenancy,
  idempotency, ETags, cursor binding, MFA/reason replay, immutable evidence and safe
  event/quarantine content are tested.
- EVT-001/EVT-002/EVT-003: `Verified for Sprint 4` — four lifecycle event types use
  the existing version-1 envelope and transactional outbox.
- TST-001: `Verified for Sprint 4` — C4-T01-C4-T24 map to executable test nodes; 116
  PostgreSQL tests at 90.97% plus migration, quality, image, scan and smoke gates pass.
- DOC-001: `In final review` — implementation/API/governance evidence is current;
  independent acceptance disposition is recorded separately.

These statuses do not implement or approve Sprint 5, Phase 3 or Phase 4.

Independent review supersedes the acceptance-candidate statuses above:
CON-001, CON-002, VAL-001, TEN-001, TEN-002, AUD-001, SEC-001, SEC-002,
TST-001 and DOC-001 are `In rework for Sprint 4`. Nine-entity PostgreSQL dispatch,
job-bound quarantine/cursors and recent-auth checking are verified remediation, but
the durable worker, functional DLQ replay, mapping-set/composite-tenant schema,
cleanup and direct negative-test gaps remain. Sprint 4 is not accepted.

### Authoritative Phase 2 Sprint 4 remediation traceability — 2026-08-05

- CON-001/CON-002/VAL-001: `Verified candidate` — generated-only registry, all-nine
  canonical dispatch, committed batches, resume, dead-letter replay, quarantine,
  reconciliation and staging cleanup pass the 120-test PostgreSQL suite.
- TEN-001/TEN-002/SEC-001/SEC-002: `Verified candidate` — composite tenant keys,
  immutable tenant triggers, forced RLS, non-bypass runtime tests, scoped APIs,
  MFA/recent-auth replay and bound cursors pass.
- EVT-001/EVT-002/EVT-003: `Verified candidate` — versioned lifecycle events remain
  transactional with canonical outcomes.
- TST-001: `Verified` — 120 passed, 91.23% coverage; complete migration,
  quality, image, Trivy, Gitleaks and live/isolation gates pass.
- DOC-001: `Verified` — governance is current and the independent final review
  accepted Sprint 4 with future-phase boundaries unchanged.

### Authoritative Phase 2 Sprint 5 design traceability — 2026-08-05

- CON-001/CON-002/VAL-001: `Designed, blocked` — real-adapter, schema, mapping,
  identity, checkpoint, quarantine and reconciliation structures are specified, but
  the pilot inputs required to bind them are absent.
- TEN-001/TEN-002/AUD-001/SEC-001/SEC-002: `Designed, blocked` — composite tenancy,
  RLS, secret/network isolation, read-only access and C5-T01-C5-T24 are specified;
  transport-specific controls cannot be finalized without transport selection.
- EVT-001/EVT-002/EVT-003: `Designed, blocked` — safe candidate events are defined,
  but exact schemas await source and threshold versions.
- TST-001: `Planned` — generated/anonymised transport, PostgreSQL, API, security and
  E2E gates are listed; no Sprint 5 implementation tests exist or are claimed.
- DOC-001: `Blocked` — requested artifacts and independent review exist; the review
  correctly withholds design approval pending the authoritative pilot package.

### Phase 3 implementation traceability — 2026-07-29

- SYS-001: `In progress` — source-system/observation persistence exists without raw
  payloads and deterministic authority dispositions cover equivalence, precedence,
  and late conflict; full observation-to-projection persistence remains.
- TEN-001/TEN-002: `In progress` — immutable tenant columns, composite keys, scoped
  policy and forced RLS exist and PostgreSQL runtime tests pass; the complete table
  and relationship matrix remains.
- DAT-001: `In progress` — core canonical models, nine concrete PostgreSQL lineage
  tables, status history, authority rules, and temporal exclusion constraints exist;
  application lineage services for every entity remain.
- DAT-002: `Implemented` — strict schemas/models exclude prohibited learner fields
  and raw payloads; masked responses and generated fixtures pass.
- AUD-001: `In progress` — implemented sensitive operations audit atomically;
  remaining operations require audit coverage.
- API-001/API-002: `In progress` — implemented routes use the approved controls,
  including reconciliation dismissal and subject-rights completion/export-manifest
  metadata; full contract acceptance remains coupled to security completion.
- SEC-002: `In progress` — permission/scope/MFA/masking/restriction/RLS controls and
  PostgreSQL append-only triggers/grants pass; the complete applicable P3-T01–P3-T26
  matrix remains.
- TST-001: `In progress` — 68 PostgreSQL tests, no skips, 90.26% coverage and all
  migration/quality/image/scan/smoke gates pass; migration immutability and
  missing-service/security tests remain.
- DOC-001: `Verified` — implemented scope, evidence, review findings, decisions,
  risks, and status are current.

Phase 3 remains unaccepted. Phase 4 has not started.

### Phase 3 final remediation candidate — 2026-07-30

- SYS-001: `Implemented` — the internal observation service persists replay-safe
  observations and lineage and applies effective authority, equivalence, precedence,
  late-arrival, projection and conflict rules.
- TEN-001/TEN-002: `Verified` — composite tenant relationships, scoped authorization,
  forced RLS and runtime-role restrictions pass PostgreSQL tests.
- DAT-001/DAT-002: `Implemented` — all nine canonical entity types have concrete
  database and application lineage, temporal/status history controls, and strict
  minimised schemas.
- API-001/API-002: `Implemented` — the approved Phase 3 routes, including generic
  lineage, reconciliation dismissal, and subject-rights completion/export-manifest,
  are present and tested.
- SEC-002: `Verified` — P3-T01–P3-T26 are bound to executable control evidence;
  PostgreSQL append-only, RLS, masking, MFA and restriction controls pass.
- TST-001: `Verified` — 73 PostgreSQL tests pass with no skips at 90.88% coverage;
  migration, quality, image, scan and smoke gates pass.
- DOC-001: `In progress` — final independent acceptance review is pending.

### Phase 3 accepted traceability — 2026-07-30

SYS-001, TEN-001, TEN-002, DAT-001, DAT-002, AUD-001, API-001, API-002,
SEC-002, TST-001 and DOC-001 are `Verified` for approved Phase 3 scope. Evidence is
the 88-test PostgreSQL suite at 90.67% coverage, complete migration lifecycles,
all-nine PostgreSQL lineage/projection/audit coverage, concurrent replay, temporal
overlap rejection, P3-T01–P3-T26 evidence, final image/scan/smoke gates, and the
independent **Accepted** decision. Phase 4 remains `Planned`.

### Authoritative Phase 2 Sprint 5 demo implementation candidate — 2026-08-05

- CON-001/CON-002/VAL-001: `Verified candidate` — fixed package resolver, compiled
  approval hash, closed schema/mapping, bounded checkpointing, quarantine and
  deterministic reconciliation pass generated happy/negative journeys.
- TEN-001/TEN-002/AUD-001/SEC-001/SEC-002: `Verified candidate` — composite tenancy,
  forced RLS, append-only schema/transport evidence, closed request models and direct
  C5-T01–C5-T24 execution pass. Production approval remains blocked.
- EVT-001/EVT-002/EVT-003: `Verified candidate` — package, sync, batch, threshold and
  completion events remain transactional and safe-value-only.
- TST-001: `Verified candidate` — 146 PostgreSQL tests pass at 91.36%; migration,
  quality, SBOM, build, zero-critical Trivy, Gitleaks and live/isolation gates pass.
- DOC-001: `In review` — API and governance evidence are current; independent
  completion review is pending.

### Authoritative Phase 2 Sprint 5 demo-design traceability — 2026-08-05

- CON-001/CON-002/VAL-001: `Verified for demo design` — the closed
  `synthetic_reference_erp_v1` adapter, generated schemas, mappings, exact identity,
  authority, checkpoint, quarantine and deterministic reconciliation rules are
  specified; no implementation is claimed.
- TEN-001/TEN-002/AUD-001/SEC-001/SEC-002: `Verified for demo design` —
  forced RLS, composite tenancy, append-only evidence, no-network/no-credential
  boundary and C5-T01–C5-T24 evidence are specified. Production controls remain
  blocked without real owner approvals.
- EVT-001/EVT-002/EVT-003: `Verified for demo design` — closed safe v1
  event types and payload constraints are frozen for the generated profile.
- TST-001: `Planned` — package validation exists; connector implementation tests and
  runtime gates cannot run until separate implementation approval.
- DOC-001: `Verified for demo design` — the concrete package and design suite were
  independently accepted after scenario and mapping completeness remediation.
  Implementation and production readiness are not claimed.

### Sprint 5 completion-review remediation traceability — 2026-08-05

This section supersedes the earlier Sprint 5 implementation-candidate evidence.
CON-001/CON-002/VAL-001 now also verify explicit enrolment-status projection and
persisted classified connector failures. EVT-001/EVT-002/EVT-003 verify correlation
metadata plus safe drift/failure events. TEN-001/TEN-002/SEC-001/SEC-002 verify the
synthetic API journey with the non-bypass PostgreSQL role and database-enforced
retention bounds. TST-001 is `Verified candidate` with **148 passed**, no skips,
**91.28% coverage**, both migration lifecycles, four zero-critical image scans,
validated 91-component SBOM, no-leak scan, and live/readiness/AI-outage/no-network
smoke evidence. DOC-001 remains `In review` pending independent re-review.

Independent re-review supersedes that pending status: DOC-001 and the Sprint 5
generated-demo package are `Accepted`. Production and real-ERP requirements remain
blocked and must not inherit this demo acceptance.

### Production First Real ERP Connector design traceability — 2026-08-05

- CON-001/CON-002/VAL-001: `Structurally designed; blocked` — closed adapter,
  checkpoint, validation, reconciliation and package boundaries are defined, but
  vendor transport/schema/mapping authority is absent.
- TEN-001/TEN-002/AUD-001/SEC-001/SEC-002: `Structurally designed; blocked` — RLS,
  secret, egress, TLS, retention and evidence requirements are specified; concrete
  production policies and named approvals are absent.
- EVT-001/EVT-002/EVT-003: `Structurally designed; blocked` — safe event metadata and
  families are defined; transport/package-specific schemas are not frozen.
- TST-001: `Planned, blocked` — transport-specific security, resilience and E2E cases
  cannot be made authoritative without the production package.
- DOC-001: `Independently accepted structural scaffold` — production design approval
  remains prohibited while entry criteria are unmet; all functional, security,
  event and test requirements remain structurally designed/planned and blocked.

### Synthetic production-like operational-validation traceability — 2026-08-05

- CON-001/CON-002/VAL-001: `Verified for generated operational simulation` — bounded
  baseline, resilience and soak profiles use only the checksum-bound adapter.
- SEC-001/SEC-002: `Verified for simulation boundary` — reports contain safe metrics/
  codes only, no network or credentials, and never claim production readiness.
- TST-001: `Verified` — 153 PostgreSQL-backed tests pass without skips at 91.38%; all
  profiles, quality/dependency gates, rebuilt-image no-network execution, health and
  zero-critical scan pass.
- DOC-001: `Independently accepted for generated operational simulation` — validation
  contract, boundary and evidence passed review. Real connector requirements remain
  blocked.

### Authoritative Phase 3 intervention entry traceability — 2026-08-05

- INT-001: `Design authorized; implementation not started` — case lifecycle, assignment, tasks, SLA/escalation, evidence, outcomes, audit and reporting require a new intervention-specific design suite.
- TEN-001/TEN-002/IAM-001/AUD-001/SEC-002: `Baseline verified; Phase 3 design pending` — existing tenant/RLS controls must be extended with workflow role/scope and negative-transition cases.
- EVT-001/EVT-002/EVT-003: `Foundation verified; contracts pending` — revision `0006` provides primitives, not approved intervention event semantics.
- AI-002: `Boundary verified for entry` — Core remains functional without AI; Phase 3 may not depend on AI or permit direct AI database writes.
- TST-001/DOC-001: `Design gate in progress` — Phase 3 acceptance tests and independent design approval are not present. No implementation is claimed.

### Authoritative Phase 3 intervention design traceability — 2026-08-05

- INT-001: `Design independently accepted; implementation not started` — human-owned cases, tasks, SLA/escalation, evidence, outcomes and reporting are defined; implementation awaits explicit user approval.
- TEN-001/TEN-002/IAM-001/AUD-001/SEC-002: `Designed for Phase 3; implementation pending` — role/scope, forced RLS, composite keys, atomic audit, privacy and C3-T01–C3-T40 are specified.
- API-001/API-002: `Designed; implementation pending` — bounded routes, replay, ETags, opaque cursors and closed schemas/errors are specified.
- EVT-001/EVT-002/EVT-003: `Designed; implementation pending` — safe versioned events reuse outbox/processed-event foundations.
- OPS-001: `Designed; implementation pending` — deterministic scheduling, projection lag, bounded retry and AI-outage operation are specified.
- TST-001: `Planned` — unit, PostgreSQL, API, security and E2E evidence is mapped.
- DOC-001: `Independently accepted design` — two remediation rounds closed privacy, mutation, subject-rights, SLA and governance findings; no implementation is claimed.
