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
