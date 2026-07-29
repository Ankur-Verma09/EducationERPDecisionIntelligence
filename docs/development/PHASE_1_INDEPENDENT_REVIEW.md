# Phase 1 Independent Engineering, Security, and SDET Review

## Review metadata

- Review date: 2026-07-28
- Scope: Phase 1 — Project Foundation
- Decision: **Rework required**
- Reviewer posture: implementation and status claims treated as untrusted until verified

## Evidence reviewed

- Original supplied requirements
- All files under `docs/development/` and `docs/api/`
- Python source under `src/`
- Alembic configuration and migration revision
- Dockerfile, Compose configuration, environment example, Make targets, and CI workflow
- All 16 automated test functions under `tests/`

No original PRD, HLD, LLD, system architecture, system design, database design, or
separate original implementation plan exists in the repository. Architectural
alignment can therefore be assessed only against the supplied mandate, Phase 0 plan,
and Phase 1 implementation plan.

## Validation performed

| Check | Result | Evidence |
|---|---|---|
| Python source/test/migration compilation | Passed | `python -m compileall -q src tests migrations` |
| `pyproject.toml` parse | Passed | Parsed with Python `tomllib` |
| Docker Compose parse/interpolation | Passed | `docker compose config` |
| Dependency installation | Blocked | PyPI HTTPS and pip build-dependency retrieval timed out |
| Ruff formatting/lint | Not run | Ruff could not be installed |
| Strict mypy | Not run | Mypy could not be installed |
| Pytest/coverage | Not run | Runtime/test dependencies could not be installed |
| Alembic migration execution | Not run | Dependencies unavailable; Docker daemon not running |
| PostgreSQL integration | Not run | Docker daemon not running |
| Container build/start | Not run | Docker daemon not running and package registry unavailable |
| CI execution | Not run | Directory is not a Git repository; no remote CI evidence |
| Secret-log probe | Failed | Formatter emitted `password=plain-secret` verbatim |

The phase exit criteria—application starts, database connects, health endpoints pass,
CI executes build/lint/tests, and no secrets are committed—have not been demonstrated.

## Critical issues

No critical issue is proven within the currently tiny, data-free operational API.
This does not permit acceptance: several high-priority correctness, security, and
verification gaps remain.

## High-priority issues

### H-01 — Complete test and static-validation evidence is absent

All 16 tests are unexecuted. Ruff, mypy, coverage, Alembic, PostgreSQL integration,
container build/start, and CI have not run. Syntax compilation cannot establish
runtime correctness. This directly fails the Phase 1 exit criteria and Definition of
Done.

**Fix:** restore an approved package registry/internal mirror, create a reproducible
lock, install from it, start PostgreSQL, run migration upgrade/downgrade/upgrade,
execute every local/CI gate, start the image, and probe live/ready/OpenAPI endpoints.

### H-02 — Log redaction does not prevent secret or personal-data leakage

`src/education_erp/logging.py:34` uses `record.getMessage()` and line 40 serializes
exception text. `redact()` only redacts values whose dictionary keys match a small
allowlist. A direct probe logged `password=plain-secret` unchanged. Exception messages,
URLs containing credentials, query strings, and free-form PII can therefore enter
logs. The traceability claim for SEC-001 is overstated.

**Fix:** adopt allowlisted structured event fields; prohibit arbitrary sensitive
messages; sanitize URLs and exception output; broaden normalized key matching; add
tests for message, exception, case/format variants, DSNs, nested values, and PII.

### H-03 — CI security controls required by the Phase 1 plan are missing

`.github/workflows/ci.yml` runs formatting, lint, typing, migrations, tests, and a
Docker build only. It does not run the planned secret scan, dependency audit, SAST,
SBOM generation, or container scan. Actions and container base images are referenced
by mutable tags rather than immutable digests/commit SHAs.

**Fix:** add and enforce secret scanning, dependency vulnerability audit, SAST, SBOM,
container scan, migration verification, and artifact provenance. Pin third-party
actions and production images immutably.

### H-04 — PostgreSQL integration is not actually tested

Tests labelled integration use SQLite in memory or a failing SQLite file path.
`tests/conftest.py:14` forces SQLite even when CI provides
`EDUERP_DATABASE_URL` for PostgreSQL. CI runs Alembic against PostgreSQL but never
executes API readiness or engine behavior against it. Driver settings, pooling,
connection failure behavior, and health semantics may differ.

**Fix:** separate fast SQLite component tests from mandatory PostgreSQL integration
tests; use the CI database URL; test successful/unavailable/timeout cases and actual
API readiness; verify migrations and schema revision.

### H-05 — Production configuration fails open

`src/education_erp/config.py` defaults to a known database credential, enables API
documentation, includes `testserver`, and accepts these values in staging/production.
The validator rejects only an empty URL. A production process can therefore start
with unsafe defaults instead of failing fast.

**Fix:** add environment-aware validation that rejects known/default credentials,
requires an explicit host allowlist, disables docs by default outside local/test,
requires approved secret injection, and validates PostgreSQL/TLS expectations.

## Medium-priority issues

### M-01 — Database readiness does not check migration/schema readiness

`SELECT 1` proves connectivity only. An application with missing or stale migrations
will report ready. Compose also starts the API without a migration job.

**Fix:** add a migration-state readiness check or deployment init job, with a clear
policy for backward-compatible rolling deployments.

### M-02 — Error handling is implemented but effectively untested

No route/test triggers validation errors or unexpected exceptions. The response
envelope, request-ID propagation, logging behavior, and secure headers on error paths
are unverified. Host-rejection response contract is undocumented.

**Fix:** add controlled test routes or isolated handler tests for 400/404/405/422/500,
including malformed input, request-ID consistency, no internal leakage, and security
headers.

### M-03 — Global logging configuration is process-global and destructive

Every `create_app()` call clears all root handlers. This is unfriendly to embedded
servers, test runners, telemetry instrumentation, and multiple app instances, and is
not concurrency-safe during initialization.

**Fix:** configure logging at process entry once or make configuration idempotent and
non-destructive; integrate correlation context without mutating global handlers per
factory call.

### M-04 — The “E2E” test is an in-process API test

It uses `TestClient` and SQLite, not the built container, Compose network, PostgreSQL,
migrations, or actual socket behavior. It does not prove the local stack starts.

**Fix:** add a Compose-based smoke/E2E test that migrates, starts services, probes
health and OpenAPI, verifies a database outage changes readiness to 503, and shuts
down cleanly.

### M-05 — Reproducibility and repository controls are incomplete

There is no dependency lock file, the project is not initialized as a Git repository,
and CI has never executed. Broad compatible version ranges can resolve differently
over time.

**Fix:** initialize version control, commit a reviewed lock/constraints file, pin CI
tooling, and retain successful CI evidence.

### M-06 — Migration downgrade/chain behavior is untested

The baseline is schema-empty and syntactically valid, but no upgrade, downgrade, or
revision-chain test ran. Autogeneration metadata is `None`, so future model drift
cannot be detected until this is changed.

**Fix:** test upgrade/downgrade/upgrade against PostgreSQL and wire application
metadata before the first schema-bearing migration.

## Low-priority issues

### L-01 — Security checklist heading is stale

It still labels the final section “Phase 0 security status” while describing Phase 1.

### L-02 — API documentation is incomplete as a formal contract

The Markdown document omits response headers and schemas in machine-verifiable form,
and OpenAPI tests check path presence only—not status codes, bodies, headers, tags,
operation IDs, or disabled-doc behavior.

### L-03 — Local database is exposed on all host interfaces by Compose

Publishing `5432:5432` is convenient but unnecessarily broad for many development
machines. Bind to `127.0.0.1` unless external access is explicitly needed.

### L-04 — Generated bytecode exists in the working directory

`__pycache__` files are ignored but present. This is harmless locally but emphasizes
that no clean-checkout CI or packaging evidence exists.

## Missing requirements or incomplete Phase 1 deliverables

- Demonstrated local application startup
- Demonstrated PostgreSQL connectivity through the API
- Passing health/readiness tests
- Executed CI build, lint, type, migration, test, and container gates
- Secret scanning, dependency audit, SAST, SBOM, and container scanning promised by
  the master/Phase 1 plan
- Reproducible locked dependencies
- Verified consistent error responses
- Verified migration lifecycle

A frontend skeleton is not considered missing because the Phase 1 plan reasonably
scoped this as a backend foundation and no UI requirements/designs exist.

## Tenant isolation, role access, privacy, idempotency, concurrency, and AI

- **Tenant isolation and RBAC:** no business records or protected business endpoints
  exist, so these cannot be verified and are not Phase 1-complete requirements. They
  remain mandatory Phase 2 gates. Health endpoints disclose only operational state.
- **Data privacy:** no institutional data is processed. Log leakage remains relevant
  and is captured in H-02.
- **Idempotency:** no write endpoint or external effect exists. Not applicable in this
  phase.
- **Concurrency:** no load/concurrency test exists. Synchronous readiness runs in
  FastAPI's worker thread, but pool saturation, outage behavior, and repeated health
  checks are unverified.
- **AI safety:** no AI component exists. Not applicable.

## Architectural alignment

The modular-monolith, adapter-ready direction and separation of future domain
features are consistent with the Phase 0 plan. The implementation correctly avoids
premature identity, tenant, ERP, and AI logic. Deviations are chiefly operational:
the promised security CI gates are absent, PostgreSQL is not exercised by tests, and
readiness is weaker than deployment readiness.

## Recommended fix order

1. Restore reproducible dependency access and initialize version control.
2. Fix log/exception redaction and production fail-fast configuration.
3. Add real PostgreSQL and migration lifecycle tests.
4. Add error-path and container/Compose E2E tests.
5. Add the missing CI security/supply-chain gates and immutable pins.
6. Run every gate, fix failures, record exact versions/results, and independently
   re-review before Phase 2.

## Phase acceptance decision

**Rework required**

The implementation is a plausible foundation skeleton, but Phase 1 cannot be accepted
because its executable correctness, security tests, database behavior, CI, and local
startup have not been demonstrated. The confirmed log-redaction weakness and missing
CI security gates also contradict current traceability/security claims. Do not begin
Phase 2 until the high-priority findings are resolved and all Phase 1 exit criteria
pass.

## Remediation update — 2026-07-28

The following changes were made in response to this review:

- H-02: free-form messages, bearer credentials, database URLs, and exception text are
  sanitized; the original direct leak probe now returns `[REDACTED]`.
- H-03: CI now includes pip consistency, Bandit, pip-audit, secret scanning, SBOM,
  container vulnerability scanning, migration cycling, and container smoke testing.
  GitHub actions are pinned to full commit SHAs.
- H-04: a mandatory environment-driven PostgreSQL readiness test was added; SQLite
  tests remain fast component tests.
- H-05: staging/production reject default credentials, local/wildcard hosts,
  interactive docs, non-PostgreSQL databases, and database connections without TLS.
- M-01/M-06: readiness checks the Alembic revision; Compose runs a migration job; CI
  performs upgrade/downgrade/upgrade.
- M-02/M-04: 422, 500, 404, stale-migration, and container smoke coverage was added.
- M-03: application factories no longer clear or reconfigure global log handlers.
- M-05: the repository is initialized as Git and direct dependency constraints exist.
- L-01/L-03: the security heading is corrected and PostgreSQL binds to loopback only.

The review decision remains **Rework required** until the 27-test suite, static
checks, real PostgreSQL lifecycle, security scans, and container smoke test execute
successfully. PyPI remains unreachable and the Docker daemon is not running in the
current environment; a fully hashed transitive lock also remains pending registry
access.

### Validation retry — 2026-07-28 23:23 IST

Acceptance gates were retried. Docker Desktop launched, but its diagnostics failed on
backend-pipe access and could not verify Hyper-V/virtualization prerequisites. PyPI
HTTPS continued to time out, with no alternate pip index or local wheel cache
available. No acceptance-blocking test changed from failed/unexecuted to passed.
Decision: **Rework required**.

## Independent revalidation — 2026-07-29

The prior report was not assumed correct. Source, tests, dependency state, and
executable gates were re-evaluated. The following claims are directly supported by
current command output:

- Ruff formatting and lint pass.
- Strict mypy passes for all 18 checked source/test files.
- Bandit reports no findings.
- pip-audit reports no known dependency vulnerabilities.
- The test suite collects 31 cases: 30 pass and the mandatory real-PostgreSQL case
  skips because no database URL can be provided without Docker.
- Coverage is 95.18%, exceeding the 90% threshold.
- A reproducible CycloneDX JSON SBOM is generated.
- The committed transitive lock contains exact versions and SHA-256 hashes.

The executable review found and corrected defects not captured by the earlier
implementation report:

1. SQLite in-memory test connections were not safely shared across worker threads.
2. Unexpected-error responses omitted correlation and baseline security headers.
3. Raw exception secrets entered pytest log capture before formatter redaction.
4. Package typing metadata and updated FastAPI test typing were incomplete.
5. Previously constrained dependency versions contained published vulnerabilities.

The corrected tests verify the affected behavior. No tenant-owned data, protected
business endpoint, RBAC implementation, write operation, concurrency-sensitive
workflow, or AI component exists in Phase 1; those controls remain future-phase
requirements and were not falsely claimed as verified.

### Remaining acceptance blockers

- Docker CLI is installed, but the current identity receives access denied from
  `//./pipe/docker_engine`.
- Therefore PostgreSQL migration upgrade/downgrade/upgrade, the real-PostgreSQL test,
  image build, image scanning, and container smoke testing remain unexecuted.
- No remote CI run evidence exists.

### Acceptance decision

**Rework required**

No currently observed local Python, code-quality, SAST, dependency, or coverage
failure remains. Acceptance is nevertheless prohibited because database correctness,
image security, and deployed-container behavior have not been demonstrated. Phase 2
must not begin.

## Docker-gate retry — 2026-07-29

Independent execution confirmed that Docker Desktop's Windows service is running,
but the Codex execution identity cannot open `//./pipe/docker_engine`. Retrying with
an empty, readable Docker client configuration produced the same access-denied
result, ruling out the inaccessible user Docker configuration as the sole cause.

All gates that do not require the Docker Engine were rerun and passed. Test results
remain 30 passed, 1 PostgreSQL test skipped, and 95.18% coverage. No new source-code
failure or vulnerability was found.

Decision: **Rework required**. The decision cannot become Accepted while PostgreSQL
migration correctness, image vulnerabilities, and deployed-container readiness are
unverified.

## Final independent acceptance — 2026-07-29

Later executable evidence supersedes the earlier blocked decisions:

- Alembic upgrade/downgrade/upgrade passed against PostgreSQL, ending at `0001`.
- The complete PostgreSQL-enabled suite passed: 32 tests, no skips, 95.18% coverage.
- The image built successfully.
- The first scan exposed four critical Debian `perl-base` vulnerabilities. The
  runtime was changed to Alpine and rebuilt; final Trivy result: 0 critical.
- Compose enforced database health and migration completion before API startup.
- The API and database became healthy; live and ready returned `status: ok`.
- Ruff, strict mypy, Bandit, pip-audit, dependency consistency, hashed-lock
  validation, and SBOM generation passed.

### Final decision

**Accepted with minor follow-up**

The minor follow-up is a retained successful remote CI run after a remote repository
is configured. It is operational evidence, not an unresolved security, isolation,
correctness, or data-loss defect. Phase 1 acceptance criteria are satisfied locally.
