# Risks and Dependencies

Scales: probability and impact are Low, Medium, or High.

| ID | Risk | Probability | Impact | Mitigation / dependency | Owner |
|---|---|---:|---:|---|---|
| R-001 | Missing PRD/designs cause incorrect scope | High | High | Obtain and approve source documents before Phase 1 decisions | Product |
| R-002 | Ambiguous tenant boundary causes data exposure | High | Critical | Define boundary; threat model; layered isolation tests | Security/Product |
| R-003 | Sensitive student data violates privacy obligations | Medium | Critical | DPIA, minimisation, purpose/consent, retention, masking | Privacy |
| R-004 | ERP schema variability breaks ingestion | High | High | Versioned mappings, contracts, quarantine, sample datasets | Integration |
| R-005 | Duplicate/out-of-order sync corrupts state | Medium | High | Source keys, checkpoints, idempotency, replay tests | Data |
| R-006 | Risk outputs cause unfair consequential treatment | Medium | Critical | Explainability, prohibited features, evaluation, human review | Data/Product |
| R-007 | AI leaks tenant data or follows injected content | Medium | Critical | Retrieval authZ, isolation, sanitisation, eval/red-team gates | AI/Security |
| R-008 | AI provides unsupported policy statements | High | High | Versioned sources, citations, abstention, output validation | AI |
| R-009 | Write-back performs duplicate/unauthorised actions | Medium | Critical | Separate credentials, confirmation, idempotency, immutable audit | Integration |
| R-010 | Unset SLO/scale creates unsuitable design | High | High | Workload model and SLO workshop before topology commitment | Platform |
| R-011 | Audit logs expose PII/secrets | Medium | High | Allowlist fields, redaction, access controls, retention | Security |
| R-012 | Dependency/supply-chain compromise | Medium | High | Lockfiles, SBOM, signed images, scanning, patch policy | Platform |
| R-013 | Incomplete backup/deletion semantics violate policy | Medium | High | Define restore and cryptographic/physical deletion procedures | Data/Privacy |
| R-014 | Dashboard exports enable bulk leakage | Medium | High | Permissioned export, limits, watermark/audit, minimisation | Product/Security |
| R-015 | Package registry is unreachable, preventing executable validation | High (current environment) | High | Restore PyPI/internal mirror access; install locked dependencies; run all gates | Platform |
| R-016 | Floating compatible dependency ranges reduce reproducibility | Medium | Medium | Generate and commit a reviewed lock file after registry access is restored | Platform |
| R-017 | Docker daemon is unavailable, blocking PostgreSQL/container validation | High (current environment) | High | Start Docker Desktop/Engine; run migration lifecycle and smoke suite | Platform |
| R-018 | Remote CI has not executed the committed workflow | Medium | High | Configure a remote repository and retain a successful protected-branch CI run | Platform |
| R-019 | Implementing Phase 2 without an approved tenant and identity trust model causes cross-tenant exposure or privilege escalation | High | Critical | Approve the tenant hierarchy, IdP/protocol, permission matrix, privacy baseline, and threat model before schema or API work | Product/Security/Privacy/Platform |
| R-026 | Implementing Phase 3 without approved canonical semantics, student-data governance, lineage, ERP authority, and education-record authorization creates unlawful collection, cross-tenant disclosure, or irreversible data corruption | High | Critical | Approve the Phase 3 glossary/scope, privacy baseline, permission matrix, lineage/merge/temporal rules, representative schemas, architecture, threat model, and API contract before implementation | Product/Data/Privacy/Security/Integration |
| R-027 | Phase 3 implementation may drift from the approved minimised schema, authority rules, concrete lineage, or layered isolation | Medium | Critical | Enforce the Phase 3 independent-review constraints, migration/schema inspection, threat-test matrix, and stop-for-design-change rule | Engineering/Data/Privacy/Security |
| R-028 | Local phase numbering can falsely imply authoritative Phase 2/3 completion | High | Critical | Apply DEC-044/045 and use authoritative names in every new status and gate | Architecture/Product |
| R-029 | AI deployment could inherit Core database credentials or starve Core resources | Medium | Critical | Closed for WP1: separate profiles/networks, no AI DB credential, bounded resources and live outage isolation passed | Platform/Security |
| R-030 | HTTP idempotency could be mistaken for event-consumer replay safety | High | High | Closed for WP1 foundation: distinct outbox/processed-event records pass real PostgreSQL replay tests | Platform/Integration |
| R-031 | Upstream PostgreSQL helper binary contains a critical toolchain vulnerability | Medium | Critical | Closed: rebuild the same `gosu` release with Go 1.25.7 and require zero-critical Trivy evidence | Platform/Security |
| R-032 | First-connector implementation without a selected pilot source, approved mapping, identity policy and numeric reconciliation gates | High | Critical | Block authoritative Phase 3 until the connector architecture and pilot approval package are explicit | Product/Integration/Data/Security/Privacy |

## Critical dependencies

- Approved PRD and prioritised release scope
- Architecture and deployment constraints
- Data classification, privacy impact assessment, and retention schedule
- Identity provider and authorisation model
- Representative, anonymised ERP schemas and samples
- Institutional policy corpus and document access rules
- Initial risk-policy definitions and historical outcome data assessment
- Supported browsers, accessibility target, and UI designs
- CI/CD platform, artifact registry, secret manager, and environments
- Named product, security, privacy, data, and operational owners

No unknown technical dependency prevents planning. Missing governance and product
inputs block Phase 2 design decisions. In Phase 1, registry connectivity is an active
validation blocker: source compiles, but runtime, lint, typing, migration, and test
execution require the declared packages. Docker daemon availability is also required
for PostgreSQL, image, vulnerability-scan, and container-smoke evidence.

## Latest dependency verification

On 2026-07-28, PyPI HTTPS timed out and the local Docker Engine pipe remained absent.
Risks R-015 and R-017 are therefore active, not hypothetical. Phase 1 acceptance and
Phase 2 entry remain blocked.

Docker diagnostics additionally confirmed that the Codex sandbox identity cannot
access Docker Desktop backend pipes and cannot verify Hyper-V prerequisites. Host
administrator/user intervention is required before R-017 can be retested.

## Dependency verification update — 2026-07-29

R-015 is resolved for the current project environment: dependencies installed from
official PyPI, the hashed lock was generated, `pip check` passed, and pip-audit found
no known vulnerabilities. R-016 is mitigated by the committed fully hashed transitive
lock.

R-017 remains active. Docker Desktop processes and the Docker CLI are present, but
the engine named pipe rejects the current identity with access denied. This blocks
PostgreSQL, migration lifecycle, image scan, and deployed smoke evidence. R-018
remains open because there is no remote CI execution record.

### Docker authorization retry — 2026-07-29

R-017 remains active after another explicit retry. `com.docker.service` is running,
but `DESKTOP-00B7QTS\CodexSandboxOnline` is denied access to the Docker Engine named
pipe. Mitigation requires launching validation from an identity/session Docker
Desktop authorizes, or exposing a securely authenticated engine endpoint to that
session. Merely starting the Docker Windows service does not satisfy this dependency.

## Final Phase 1 risk disposition — 2026-07-29

- R-015 is closed: registry access, installation, lock generation, and audit passed.
- R-016 is mitigated by the fully hashed transitive lock.
- R-017 is closed for validation: Docker gates executed from the authorized account.
- R-018 remains a medium operational follow-up until remote CI evidence is retained.
- The inherited Debian critical-vulnerability risk was remediated with Alpine; the
  final image scan reports zero critical vulnerabilities.

## Phase 2 entry risk — 2026-07-29

R-002 and R-019 are active critical blockers. The example institution entities and
user roles in the original mandate are not an approved legal tenant boundary or
permission model. No Phase 2 code or migration may be represented as secure until
the required owners approve these inputs.

### Phase 2 approval update

R-002 and R-019 are mitigated at design entry by the approved institution tenant
boundary, explicit membership model, OIDC trust, permission matrix, threat model and
layered RLS policy. They remain high-consequence implementation risks and require the
full negative isolation/authorization test matrix before Phase 2 acceptance.

## Phase 2 implementation risk update — 2026-07-29

- R-020 (critical, corrected): the local/CI application credential was the PostgreSQL
  bootstrap superuser and therefore bypassed RLS. Runtime and migration roles are now
  separated, CI asserts a non-bypass identity, and the real RLS test passes.
- R-021 (high, active): the Docker image/scan/smoke evidence has not been rerun for
  Phase 2 because the Codex sandbox token cannot access Docker Desktop's engine pipe.
- R-022 (high, active): approved Phase 2 endpoint, lifecycle, idempotency,
  concurrency, support-access, and negative-test scope remains incomplete.

## Phase 2 final risk disposition — 2026-07-29

- R-020 remains closed by the separate `NOSUPERUSER NOBYPASSRLS` runtime role.
- R-021 is closed: final image/Trivy/Compose/smoke gates passed.
- R-022 is closed: persistent replay, opaque cursors, remaining endpoints,
  scoped-delegation boundaries and expanded negative tests pass.
- R-018 remains an operational follow-up until protected remote CI evidence exists;
  it is not a Phase 2 correctness or security blocker.

### Semantic audit risk disposition

- R-023 (high, closed): modifying applied migration `0003` would have left existing
  databases without role-assignment versions. Revision `0003` is preserved and
  additive `0004` passes existing-database and full lifecycle tests.
- Contract drift for idempotency headers, role-revocation preconditions and deletion
  approval is closed by executable OpenAPI and negative API tests.

### PostgreSQL API-runtime parity risk disposition

- R-024 (critical, closed): platform lifecycle routes lacked tenant context for
  RLS-protected policy/audit records. Real PostgreSQL API lifecycle tests now pass.
- R-025 (medium, closed): CI SBOM generation used an unsupported CycloneDX option.
  CI/Makefile now use `--outfile`, and the generated SBOM validates.

## Phase 3 entry risk — 2026-07-29

R-026 is active and blocks Phase 3 implementation. R-003 and R-013 also remain
unresolved for canonical student/education data. The repository has no approved
Phase 3 architecture or representative anonymised ERP schema, and the Phase 2
permission model does not define education-record access. The mitigation and exact
required inputs are documented in `PHASE_3_ENTRY_CRITERIA_ASSESSMENT.md`.

### Phase 3 design approval risk update

- R-026 is mitigated at design entry by the approved privacy model, glossary,
  generated schemas, HLD, LLD, data model, threat model, API contract, implementation
  plan, decisions, and independent review.
- R-003 remains high-consequence but is mitigated for first-release design by treating
  every learner as potentially a child, aggressively minimizing fields, prohibiting
  sensitive categories, and requiring deployment-specific lawful-basis approval.
- R-013 remains an operational dependency: Phase 3 stores retention/deletion
  eligibility and subject-rights state but does not physically delete records or
  artifacts.
- R-027 is active for implementation and cannot close until schema inspection,
  tenant/RLS/security/privacy tests, migrations, and all executable gates pass.

Phase 3 is ready for implementation but not accepted. Phase 4 remains prohibited.

### Phase 3 implementation risk update

R-027 remains active. Layered tenant isolation, strict minimisation, masking,
processing restriction, additive migration, tests, image, and scan gates pass.
Database remediation now supplies nine concrete lineage tables, temporal exclusion
constraints, status history, PostgreSQL append-only enforcement, and the remaining
approved endpoints. However, revision `0005` still imports mutable application
metadata, application lineage and observation-to-projection services are incomplete
for every approved entity, and the applicable P3-T01–P3-T26 matrix is not fully
automated. These remain high-consequence correctness/compliance gaps. Phase 3
acceptance and Phase 4 entry are blocked until they are resolved and independently
reviewed.

### Phase 3 final remediation candidate — 2026-07-30

R-027 remains active. Revision `0005` self-containment and nine-entity lineage are
closed, and all PostgreSQL, migration, quality, image, scan and smoke gates pass.
Independent review found incomplete direct threat execution, insufficient cursor
binding, incomplete effective-time/source-authority reconciliation checks and
PostgreSQL race coverage, missing audit-reason persistence, and incorrect
nonexistent-lineage behavior. Deployment risks R-003 and R-013 remain governed
production prerequisites and are not expanded into Phase 4 work.

### Phase 3 acceptance risk disposition — 2026-07-30

R-027 is closed. All implementation and independent-review findings pass executable
evidence. R-003 and R-013 remain deployment prerequisites concerning
jurisdiction-specific lawful basis, retention shortening, legal holds, encryption
keys and controller procedures; they are documented limitations rather than missing
Phase 3 functionality. No Phase 4 risk has been activated.

### Authoritative Work Package 1 risk disposition — 2026-07-30

- R-029 (closed): Docker Desktop's missing engine pipe was resolved by the host
  upgrade; the full container gate set now executes on engine 29.6.2.
- R-030 (closed): Windows bind-mounted PostgreSQL initialization stalled after the
  Docker upgrade. A derived PostgreSQL image now embeds the reviewed initialization
  script, and full migration/runtime tests pass.
- R-031 (closed): the upstream PostgreSQL Alpine image contained a critical
  vulnerability in its prebuilt `gosu`. The derived image replaces it with the same
  release compiled using Go 1.25.7; Trivy reports 0 critical findings.
- AI failure propagation and unintended database access are controlled by internal
  boundary networks, absence of AI database credentials/host ports, and a live
  stop-AI/Core-remains-healthy test.

Connector delivery, synchronization semantics, intervention workflows and AI
services remain future-scope risks and were not activated or implemented here.

### Authoritative Phase 3 entry risk — 2026-07-30

R-032 is active and blocks implementation. The authoritative roadmap requires one
read-only pilot connector and measurable completeness, freshness and reconciliation,
but the repository has no selected ERP, representative approved source schema,
source-specific mapping, transport/credential policy, identity-resolution policy,
numeric thresholds or connector-specific HLD/LLD/API/threat model. Generic canonical
and event foundations do not resolve these source-bound decisions.

### Authoritative Phase 2 Sprint 4 design risk update — 2026-08-05

- R-032 remains active for Sprint 5, the first real ERP connector. It does not block
  Sprint 4 because Sprint 4 accepts generated fixtures only and enables no external
  transport, customer credential or source-bound threshold.
- R-033 (high, design-mitigated): a generic framework could accidentally expose a
  transport, SSRF, secret or raw-data surface. The reviewed design uses a closed
  `generated_mock_v1` registry, rejects URL/path/SQL/credential fields, requires no
  egress, and mandates C4-T03-C4-T06 negative tests before acceptance.
- R-034 (high, active for implementation): incorrect job leasing or checkpoint
  acknowledgement could duplicate or skip canonical observations. Transactional
  outcomes, post-commit watermarking, persistent idempotency and kill/resume E2E
  evidence are mandatory before closure.
- R-035 (high, active for implementation): connector worker access could bypass
  canonical authority or tenant controls. Dispatcher-only access, non-bypass RLS,
  composite tenant constraints and direct-write negative tests are mandatory.

No implementation risk is claimed closed by design review. Phase 3 intervention and
Phase 4 AI risks are not activated.

### Authoritative Phase 2 Sprint 4 implementation risk disposition — 2026-08-05

- R-033 is closed for Sprint 4 by the database/app mock-only allowlist, disabled
  credential rows, closed request schemas, generated fixtures and C4-T03-C4-T06.
- R-034 is closed for Sprint 4 by transactional batch/watermark persistence,
  observation/staging deduplication, rollback/resume E2E and duplicate manifests.
- R-035 is closed for Sprint 4 by canonical-service-only dispatch, forced RLS on all
  connector tables, runtime-role negatives and authority/lineage tests.
- R-036 (closed): dependency audit found three `cryptography 48.0.1` advisories.
  Version 50.0.0 with verified platform hashes passes audit, builds and tests.
- R-032 remains active and blocks Sprint 5. Generated fixture thresholds and mock
  authority must not be reused as real-pilot policy.

No Phase 3 intervention or Phase 4 AI risk has been activated.

Independent review reopens R-034 and R-035. R-034 remains active until committed
per-batch recovery and real dead-letter replay pass. R-035 remains active until
mapping sets, composite tenant foreign keys, tenant immutability, append-only grants
and the missing direct security cases pass. R-033 remains closed for the generated-
only transport/credential boundary. R-036 remains closed by `cryptography 50.0.0`.

### Sprint 4 remediation risk reassessment — 2026-08-05

- R-034 is closed for the generated-mock milestone by committed one-batch
  transactions, `SKIP LOCKED` claiming, same-job watermark resume, persistent
  deduplication, functional dead-letter replay and expiry cleanup tests.
- R-035 is closed for the generated-mock milestone by mapping sets, composite
  tenant foreign keys, immutable tenant triggers, forced RLS, restricted runtime
  grants and all-nine canonical observation dispatch.
- R-033 and R-036 remain closed. R-032 remains active and continues to block a real
  ERP connector until the authoritative pilot inventory and thresholds exist.
- Residual operational risk: a production worker deployment/scheduler is deferred
  to the separately approved real-connector milestone; the Sprint 4 worker contract
  and recovery service are implemented and tested without external transport.

### Authoritative Phase 2 Sprint 5 design risks — 2026-08-05

- R-032 remains active and is the entry blocker: the authoritative pilot package is
  absent. Invented pilot facts could silently corrupt canonical data or accept an
  unsafe integration.
- R-037 (critical, active): transport selection may introduce SSRF, credential,
  certificate, injection, write-scope or retry-amplification risks. It cannot be
  mitigated to acceptance until the protocol and network policy are approved.
- R-038 (high, active): unapproved mappings, identity rules or source authority may
  misidentify learners or overwrite authoritative records. Fail-closed schema,
  ambiguity reconciliation and non-overwrite tests are mandatory.
- R-039 (high, active): absent numeric thresholds make completeness/freshness and
  reconciliation acceptance subjective. No mock threshold may be reused.
- R-040 (high, active): absent landing/quarantine policy risks excess child-data
  retention and incomplete deletion/rights handling.

These risks block design approval and implementation. No Phase 3 or Phase 4 risk is
activated by this design-only work.

### Sprint 5 demo-design risk reassessment — 2026-08-05

- R-032 remains active for a real ERP connector, but no longer blocks review of the
  generated demo profile. The demo package is not real-source authority.
- R-037 is avoided for the demo by an in-process adapter with no socket, credential,
  URL/path/host input or TLS surface. Any real transport reactivates the full risk.
- R-038 and R-039 are design-mitigated only for generated demonstrations through
  frozen mock mapping/identity/authority and deterministic thresholds. They remain
  active for production.
- R-040 is design-mitigated for generated data by 24-hour landing and seven-day
  quarantine limits; a real child-data lifecycle still requires privacy approval.
- R-041 (high, active for implementation): a demo-only connector could be enabled
  outside the demo profile. A database allowlist, startup guard, no-egress tests and
  deployment documentation are mandatory before demo implementation acceptance.

No production risk is closed, and no implementation risk is claimed closed by this
design approval.

### Sprint 5 demo implementation risk disposition — 2026-08-05

- R-041 is closed for the generated demo profile by the compiled manifest approval
  hash, database kind/transport constraints, fixed package resolver, Docker
  `--network none` package smoke, and negative URL/path/host/credential/TLS tests.
- R-037 is closed only for the absent demo transport surface. It reactivates for any
  CSV/SFTP/API/read-replica or customer credential proposal.
- R-038/R-039/R-040 are controlled for generated demonstration by immutable mapping,
  identity/authority/threshold snapshots, ambiguity/late-arrival tests, deterministic
  promotion blocking and bounded staging/quarantine. They remain active for real data.
- R-032 remains active and blocks production or a real ERP connector. No demo evidence
  substitutes for product, source, privacy or security owner approval.

No Phase 3 intervention or Phase 4 AI risk was activated.

Completion-review rework closed status-loss, rollback-on-transport-failure,
PostgreSQL API-evidence, event-correlation and retention-enforcement gaps. Residual
R-032 remains active: no real vendor/product/version, production owner approval,
credential path or external transport exists. The `0007` checksum is protected
prospectively, but historic immutability before its 2026-08-05 capture cannot be
proven and remains an explicit evidence limitation.

### Production First Real ERP Connector design gate — 2026-08-05

R-032, R-037, R-038, R-039 and R-040 remain active and blocking. The repository has
no production package, selected transport, source schema/mapping authority, identity
rules, network/credential policy, real-data privacy lifecycle, numeric thresholds or
named production approvals. Reusing the demo package would violate its manifest and
create high-impact tenant, child-data and source-integrity risk. Mitigation is the
checksum-bound package defined in
`PRODUCTION_FIRST_REAL_ERP_CONNECTOR_PACKAGE_REQUIREMENTS.md`, followed by independent
design re-review. No implementation or later-phase risk has been activated.

### Synthetic production-like validation risk disposition — 2026-08-05

The harness reduces uncertainty about deterministic extraction repetition, bounded
pagination, safe failure classification and container execution. It does not reduce
R-032/R-037/R-038/R-039/R-040 for a real ERP: it measures neither external transport,
PostgreSQL service throughput at scale, real schema/identity quality, production SLOs,
RPO/RTO nor production privacy behavior. The mandatory `production_ready=false` and
no-network execution prevent simulation evidence from being promoted accidentally.

### Authoritative Phase 3 entry risk reassessment — 2026-08-05

- R-032/R-037/R-038/R-039/R-040 remain active for real-pilot and production use; generated mappings or thresholds are not real-source authority.
- R-042 (high, active): historical `PHASE_3_*` names describe canonical work now credited to Phase 2. A distinctly named intervention design suite and explicit approval prevent wrong-scope authorization.
- R-043 (high, active): synthetic behavior may omit real ERP timing, identity and correction patterns. Provider-neutral workflow design may proceed, but real-pilot acceptance remains blocked.
- R-044 (critical, inactive until design): workflow defects could permit cross-tenant case access, invalid transitions, evidence leakage or unaudited consequential action. The threat model and negative-security matrix must mitigate this before implementation approval.

These risks permit design work only. They do not authorize Phase 3 implementation or Phase 4 AI.

### Authoritative Phase 3 design-candidate risks — 2026-08-05

- R-044 is activated for design and addressed by C3-T01–C3-T40, forced RLS, composite tenant keys, deterministic transitions and atomic audit/outbox requirements; it remains open until executable evidence passes.
- R-045 (high, active): case content could capture prohibited child data. Free text is excluded; closed codes/references, database constraints, schema rejection and leakage tests are required.
- R-046 (high, active): SLA/escalation may duplicate or authorize action under concurrency. Immutable snapshots, unique breach keys, `SKIP LOCKED`, proposal-only escalation and race tests are required.
- R-047 (high, active): report dimensions may enable small-cohort inference. Server scope, suppression and inference-boundary tests are mandatory.
- R-048 (critical, active): future AI could become an undeclared dependency/direct writer. Phase 3 imports no AI client/config; Core-only, stop-AI and no-DB-access tests are mandatory.

Design controls do not close implementation risks. Real ERP and production privacy dependencies remain unchanged.
