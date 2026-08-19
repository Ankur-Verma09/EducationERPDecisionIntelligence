# Development Status

## Current phase

Authoritative Phase 2 — Canonical Data and ERP Integration (**accepted for generated scope**);
Authoritative Phase 3 — Core Intervention Workflow (**design independently accepted;
implementation not approved and not started**). Phase 4 has not started.

## Remediation completed

- Production/staging configuration now fails closed for unsafe credentials, hosts,
  interactive docs, database type, and missing database TLS.
- Structured logs sanitize credential fields, free-form secrets, bearer tokens,
  database URLs, and exception text.
- Database readiness requires both connectivity and Alembic revision `0001`.
- Compose runs migrations before starting the API and includes an API health check.
- PostgreSQL binds to host loopback only.
- Error-path, stale-schema, deployed-config, redaction, and real-PostgreSQL tests were
  added; the suite now contains 27 test functions.
- CI cycles migrations, runs lint/type/tests, SAST, dependency audit, secret scan,
  SBOM generation, image scan, and container smoke testing.
- GitHub actions are pinned to full commit SHAs.
- Direct dependencies have exact constraints; a fully transitive hashed lock remains
  pending registry access.
- The directory is initialized as a Git repository.

## Validation results

| Validation | Result |
|---|---|
| Python source/test/migration compilation | Passed after remediation |
| `pyproject.toml` parse | Passed |
| Docker Compose configuration | Passed after remediation |
| Direct credential-log probe | Passed: secret replaced with `[REDACTED]` |
| Git repository initialization | Passed |
| Dependency installation | Blocked: approved/public registry HTTPS timeout |
| Ruff, mypy, Bandit, pip-audit | Not run: packages unavailable |
| 27-test pytest suite and coverage | Not run: packages unavailable |
| Alembic PostgreSQL lifecycle | Not run: packages unavailable; Docker daemon stopped |
| Image build/scan/container smoke | Not run: Docker daemon stopped |
| Remote CI | Not run: no remote repository configured |

The host global Python still reports a broken `_distutils_hack`; project execution is
expected through `.venv` after dependencies become available.

## Phase acceptance

Phase 1 remains **not complete** and the independent decision remains **Rework
required** until all executable gates pass. Phase 2 must not begin.

## Latest execution attempt — 2026-07-28

The next-phase request was evaluated against the documented boundary and treated as a
Phase 1 completion attempt because Phase 1 is not accepted.

| Check | Latest result |
|---|---|
| Original HLD/LLD/system architecture/system design | Absent; zero matching documents |
| Python package registry | Blocked: `https://pypi.org/simple/hatchling/` timed out |
| Docker Engine | Blocked: Windows Docker engine pipe is absent |
| Python compilation | Passed |
| TOML parsing | Passed |
| Compose parsing | Passed |
| Credential-redaction probe | Passed |
| Git repository access | Passed |
| Test inventory | 27 functions present; execution blocked by dependencies |

No source, API, or migration change was appropriate during this attempt. Starting
Phase 2 would violate DEC-012 and the explicit Phase 1 acceptance gate.

## Host validation attempt — 2026-07-28 23:23 IST

- Docker Desktop was launched both hidden and interactively.
- `com.docker.service` is running, but the Docker Engine pipe was never created.
- Docker's official diagnostics reported access denied to
  `\\.\pipe\dockerBackendV2` and could not verify the Hyper-V bootloader/features.
- The diagnostics recommended enabling the Microsoft hypervisor at boot and verifying
  Hyper-V/virtualization, but those host-administrator changes are outside this
  sandbox's authority.
- Direct HTTPS requests to `https://pypi.org/simple/` timed out.
- No pip proxy, alternate index, or cached Phase 1 wheels were available.

Consequently, dependency installation, hashed lock generation, executable Python
gates, PostgreSQL, image scanning, and container smoke testing remain blocked. The
independent acceptance decision remains **Rework required**.

## Exact next prompt

> Complete Phase 1 validation for `E:\EducationERPDecisionIntelligence`: provide an
> approved reachable Python package registry, start Docker Desktop/Engine, install
> from `requirements/constraints.txt`, generate a fully hashed transitive lock, run
> Ruff, strict mypy, Bandit, pip-audit, the complete 27-test pytest suite with
> coverage, Alembic upgrade/downgrade/upgrade against PostgreSQL, build and scan the
> image, run the container smoke test, fix every failure, and update the acceptance
> review. Do not begin Phase 2 unless all gates pass.

## Phase 1 validation update — 2026-07-29

The Python packaging failure was repaired by using the project virtual environment
instead of the broken global Python installation. Official PyPI was reachable with
the approved command-line trust configuration. Dependencies were upgraded to remove
all reported vulnerabilities, and a fully transitive SHA-256 hashed lock was
generated at `requirements/requirements.lock`.

| Gate | Verified result |
|---|---|
| `pip check` | Passed; no broken requirements |
| Fully hashed lock | Generated: 85 packages and 1,442 SHA-256 hashes |
| Hashed-lock structural install check | Passed with `--require-hashes --no-deps --no-index` against the installed environment |
| Ruff format | Passed; 21 files formatted |
| Ruff lint | Passed |
| Strict mypy | Passed; 18 files checked |
| Bandit | Passed; zero findings in source and lock-generation script |
| pip-audit | Passed; no known vulnerabilities (the local unpublished project is correctly skipped) |
| Pytest | 30 passed, 1 skipped |
| Coverage | Passed at 95.18%, above the 90% gate |
| SBOM | CycloneDX JSON generated and validated |
| PostgreSQL integration test | Skipped because Docker/PostgreSQL is unavailable |
| Docker Engine | Blocked: access denied to `//./pipe/docker_engine` |
| Alembic PostgreSQL cycle | Blocked by Docker Engine access |
| Image build and scan | Blocked by Docker Engine access |
| Container smoke test | Blocked by Docker Engine access |
| Remote CI | Not run; no configured remote execution evidence |

Failures found during executable validation were fixed: SQLite in-memory tests now
share a thread-safe connection pool, exception responses retain request/security
headers, exception logs redact secret material before capture, package typing metadata
is present, and the test suite is compatible with the constrained FastAPI release.

Phase 1 remains **not complete** and the independent decision remains **Rework
required**. The remaining acceptance work requires host access to a running Docker
Engine. Phase 2 must not begin.

### Exact continuation prompt

> Continue Phase 1 validation for `E:\EducationERPDecisionIntelligence` after granting
> the current user access to the running Docker Desktop/Engine. Run the PostgreSQL
> Alembic upgrade/downgrade/upgrade cycle, the mandatory PostgreSQL integration test,
> Docker image build, image vulnerability scan, and container smoke test. Fix every
> failure, rerun all local gates, update governance evidence and independently decide
> Phase 1 acceptance. Do not begin Phase 2 unless every gate passes.

## Docker access revalidation — 2026-07-29

Docker Desktop was reported as granted and the remaining acceptance gates were
retried. The Windows service `com.docker.service` is running, but the executing
identity is `DESKTOP-00B7QTS\CodexSandboxOnline`, which still receives:

```text
open //./pipe/docker_engine: Access is denied.
```

The same identity cannot read `C:\Users\Ankur\.docker\config.json`. A clean temporary
Docker configuration excluded the inaccessible client configuration as the cause;
engine access still failed. This is a Windows session-token/named-pipe authorization
blocker rather than a project defect.

The complete local gate set was rerun. `pip check`, Ruff format/lint, strict mypy,
Bandit, pip-audit, CycloneDX SBOM generation, and hashed-lock validation passed.
Thirty tests passed; the single real-PostgreSQL test skipped, and coverage remained
95.18%.

The Alembic PostgreSQL cycle, mandatory PostgreSQL test, image build, image scan, and
container smoke test remain unexecuted. Phase 1 remains **Rework required**, and
Phase 2 remains prohibited.

## Final Phase 1 validation — 2026-07-29

Later evidence supersedes the earlier blocked attempts above.

| Gate | Final result |
|---|---|
| Dependency consistency and hashed lock | Passed |
| Ruff format/lint and strict mypy | Passed |
| Bandit and pip-audit | Passed; no findings/known vulnerabilities |
| PostgreSQL-enabled pytest | 32 passed, no skips, 95.18% coverage |
| Alembic PostgreSQL lifecycle | Upgrade/downgrade/upgrade passed; `0001 (head)` |
| Image build | Passed |
| Image vulnerability scan | Passed after Alpine remediation; 0 critical |
| Migration-first Compose startup | Passed |
| Container smoke test | Live and ready returned `status: ok`; API and database healthy |
| Clean shutdown | Passed |

Container environment parsing was fixed to accept comma-separated allowed hosts
through the real settings source. The Debian runtime with four critical `perl-base`
findings was replaced by Alpine, and the rebuilt image reports zero critical
vulnerabilities.

Independent decision: **Accepted with minor follow-up**. The follow-up is to retain a
successful remote CI run when a remote repository is configured. No critical
security, isolation, correctness, migration, or data-loss finding remains in Phase 1.
Phase 2 has not been started.

## Phase 2 entry assessment — 2026-07-29

The next approved phase is Phase 2 — Identity, Institution, and Multi-Tenancy.
Implementation did not begin because critical entry criteria are unmet. The legal
tenant boundary/hierarchy, identity provider and protocol, MFA policy, role-permission
matrix, user-to-tenant membership rules, privacy/compliance baseline, threat model,
support/impersonation policy, and deployment trust boundaries are not approved.

Proceeding would require inventing security and legal boundaries and could cause
cross-tenant disclosure or an incompatible authentication architecture. Detailed
evidence, required approvals, and the conditional task list are recorded in
`docs/development/PHASE_2_ENTRY_CRITERIA_ASSESSMENT.md`.

Current state: **Phase 2 entry blocked; Phase 2 not started**.

## Phase 2 design approval and entry reassessment — 2026-07-29

The Phase 2 security model, HLD, LLD, threat model, data model, API contract and
implementation plan are approved and documented. The reassessment resolves the
tenant boundary, identity protocol, MFA, roles/permissions, multi-membership,
support-access, privacy, retention, RLS, onboarding and secret-management criteria.

Current state: **Phase 2 entry criteria met; ready for implementation; no Phase 2
application code has started**.

## Phase 2 implementation update — 2026-07-29

Phase 2 is **in progress**. Implemented foundations include deployed OIDC fail-closed
configuration, asymmetric JWT/JWKS verification, persisted platform roles, explicit
tenant memberships, built-in RBAC, transaction-local tenant context, Phase 2 schema
and migration `0002`, forced PostgreSQL RLS policies, immutable audit records,
institution onboarding, membership creation, role assignment and core protected APIs.

Local results: Ruff, strict mypy, Bandit and pip-audit pass; 46 tests pass and two
PostgreSQL-only tests skip without a database URL; coverage is 91.23%. The JWT
dependencies were upgraded after pip-audit identified vulnerable initial versions.

Phase 2 is not complete. PostgreSQL migration/RLS execution, full Docker/image gates,
and the remaining approved API/lifecycle/idempotency/support-access work are pending.

## Phase 2 PostgreSQL validation update — 2026-07-29

The real PostgreSQL `0001 -> 0002 -> 0001 -> 0002` lifecycle now passes. Validation
found and corrected two PostgreSQL-only defects:

- composite unique constraints generated duplicate names under the naming convention;
- the application used the PostgreSQL bootstrap superuser, which bypasses RLS even
  when a table uses `FORCE ROW LEVEL SECURITY`.

Compose and CI now separate the migration owner from the `education_erp_app`
`NOSUPERUSER NOBYPASSRLS` runtime login. The mandatory tenant-switch and
pooled-connection RLS test passes using that runtime identity. The full PostgreSQL
suite passes: **48 passed**, **90.97% coverage**. Ruff format/lint, strict mypy,
Bandit, and pip-audit pass.

Docker image build, scan, and smoke could not be rerun from the Codex sandbox because
its Windows token is denied access to `//./pipe/docker_engine`. This is host execution
evidence still required for the Phase 2 image.

Phase 2 remains **in progress** and independent acceptance remains **Rework
required**. Approved lifecycle, idempotency, pagination, precondition, support-access,
and full endpoint/test coverage are not yet implemented. Phase 3 must not begin.

## Phase 2 blocker-remediation update — 2026-07-29

Migration `0003` adds support-access and idempotency persistence and completes the
institution deletion-state column. Implemented APIs now cover institution
activation/suspension/update, campus and department administration, membership
listing and lifecycle transitions, last-owner protection, role listing/revocation,
tenant security policy, and expiring support-access approval/revocation. Mutable
resources enforce ETag preconditions where implemented. Suspended institutions now
lose tenant context immediately and expired assignments no longer contribute
permissions.

Validation:

- Ruff formatting/lint, strict mypy and Bandit: passed.
- pip-audit: no known vulnerabilities.
- PostgreSQL tests: 50 passed at 90.15% coverage.
- Alembic full lifecycle: `0003 -> base -> 0003` passed.
- Docker image gates: blocked because the Codex sandbox Windows token receives
  `Access is denied` from `//./pipe/docker_engine`.

Phase 2 is still not accepted. Persistent request replay for every mutation, opaque
cursor pagination, the remaining contract endpoints, full scoped-delegation matrix,
and Docker image/scan/smoke evidence remain required.

## Phase 2 blocker-remediation completion — 2026-07-29

Retained completed evidence: 50 PostgreSQL tests passed at 90.15% coverage;
Alembic revision `0003` passed; database and API containers were healthy; the
migration container completed successfully; and Trivy reported 0 critical
vulnerabilities with exit code 0.

The remaining approved blockers are implemented: persistent replay for every
mutation, opaque cursor collection envelopes, the remaining approved contract
endpoints, hierarchy-bound delegation, and expanded negative security tests. Audit
access requires MFA and is itself audited.

Final evidence from the exact remediated source:

| Gate | Result |
|---|---|
| Ruff, strict mypy, Bandit | Passed; zero findings |
| Dependency consistency and pip-audit | Passed; no known vulnerabilities |
| Secret scan and SBOM | Passed; no source/config leaks; SBOM generated |
| PostgreSQL pytest | 54 passed, no skips, 90.06% coverage |
| Alembic lifecycle | `base -> 0003 -> base -> 0003` passed; `0003 (head)` |
| Final image and Trivy | Built; exit code 0; 0 critical vulnerabilities |
| Compose | API/database healthy; migration exited 0 |
| Smoke | Live and ready returned `{"status":"ok"}` |

Phase 2 remediation is complete. Phase 3 has not started.

## Phase 3 entry assessment — 2026-07-29

The next planned phase is Phase 3 — Canonical Education Model. Phase 2 is locally
accepted, but Phase 3 is not yet approved for implementation. No Phase 3 HLD, LLD,
data model, system design, API contract, threat model, privacy baseline, permission
matrix, or implementation plan exists. Representative anonymised ERP schemas and
approved lineage, identifier, temporal, merge, retention, deletion, and ERP-authority
rules are also absent.

The Phase 2 approved architecture explicitly excludes student and education-domain
records. Creating canonical tables or endpoints without the missing decisions would
invent sensitive-data and access boundaries. `PHASE_3_ENTRY_CRITERIA_ASSESSMENT.md`
records the requirement mapping, entry evidence, blocking inputs, and detailed
conditional task list.

Current decision: **Phase 3 blocked at entry; no application code, API, or migration
started.**

### Phase 3 design approval and entry reassessment — 2026-07-29

The user authorized a conservative Phase 3 definition using generated or
irreversibly anonymised examples only. Approved artifacts now define the security and
privacy model, canonical glossary and schemas, HLD, LLD, relational model, threat
model, API contract, implementation plan, and independent design review.

The approved first release covers academic structure, minimised tenant-local learner
keys, enrolments, teaching assignments as non-authorizing data, immutable source
observations/lineage, reconciliation, processing restriction, and subject-rights
metadata. It excludes raw payloads, demographics, contacts, guardians, grades,
attendance, finance, health, discipline, notes, risk/AI, connectors, student/parent
access, physical deletion, and all Phase 4 work.

Reassessed state: **Phase 3 entry criteria met; approved and ready for implementation;
no Phase 3 application code, API, migration, or test has started. Phase 4 has not
started.**

## Phase 3 implementation update — 2026-07-29

Phase 3 is **in progress**. Implemented work includes additive revision `0005`,
canonical academic/learner/enrolment/source/lineage/privacy models, Phase 3
permissions and scoped policy, strict APIs, masked identifiers, processing
restriction, protected reveal, reconciliation, subject-rights request metadata,
forced RLS, runtime grants, audit, idempotency, ETags, and opaque pagination.

Executable evidence passes: 68 PostgreSQL tests with no skips at 90.26% coverage;
Ruff, strict mypy, Bandit, pip-audit and `pip check`; `0005 -> 0004 -> 0005` and full
`0005 -> base -> 0005` migrations; SBOM; rebuilt image; Trivy 0 critical with exit
code 0; no Gitleaks findings; healthy API/database; migration exit 0; and live/ready
smoke.

Independent completion review is **Rework required**. Database-level lineage,
temporal overlap, status-history and append-only controls and the remaining approved
routes are now present. Application lineage and observation-to-projection services
remain incomplete for every approved entity, the full applicable threat matrix is
not automated, and revision `0005` must be made self-contained instead of importing
mutable application metadata. Phase 3 is not complete or accepted. Phase 4 has not
started.

### Phase 3 remediation continuation

Reconciliation dismissal, subject-rights completion/export-manifest metadata,
enrolment status-history recording, and deterministic source-authority dispositions
for creation, equivalence, precedence, and late conflict are now implemented.

The hardened PostgreSQL result is 68 passed with no skips and 90.26% coverage.
Fresh upgrade, `0005 -> 0004 -> 0005`, and `0005 -> base -> 0005` pass, with
`0005` restored at head. PostgreSQL verifies nine concrete lineage tables, four
temporal exclusion constraints, enrolment status history, immutable-history
triggers, forced RLS, and restricted runtime grants. The rebuilt API/database are
healthy, migration exits 0, live/ready smoke returns `ok`, Trivy reports zero
critical vulnerabilities with exit code 0, and Gitleaks reports no leaks.

Revision `0005` is still not self-contained because it imports mutable application
metadata. Application-level lineage persistence/retrieval and full
observation-to-projection reconciliation are not complete for every approved entity,
and every applicable P3-T01–P3-T26 case is not yet automated. Phase 3 therefore
remains **Rework required**. Phase 4 has not started.

### Phase 3 final remediation candidate — 2026-07-30

Revision `0005` now owns explicit table definitions and imports no application
persistence metadata; revisions `0001`–`0004` remain unchanged. Application models
and the generic MFA-protected lineage route cover all nine approved canonical entity
types. The internal observation service persists idempotent observations and
lineage, resolves effective source authority, applies deterministic equivalence,
precedence and late-arrival rules, invokes projection updates for create/supersede,
and opens reconciliation issues for unresolved conflicts.

The threat traceability test requires P3-T01–P3-T26 to map to named test nodes.
Final PostgreSQL evidence is 73 passed with no skips and 90.88% coverage.
The full base-to-head lifecycle and `0005 -> 0004 -> 0005` pass. Ruff, strict mypy,
Bandit and dependency consistency pass; dependency versions are unchanged from the
previous successful pip-audit. The rebuilt API/database are healthy, migration exits
0, live/ready smoke returns `ok`, Trivy reports zero critical vulnerabilities with
exit code 0, and Gitleaks reports no leaks.

Independent final review remains **Rework required**. Direct negative execution is
missing for several threat cases; cursors lack signed tenant/route/filter/expiry
binding; reconciliation lacks separate effective time and complete authority/source
checks plus PostgreSQL race/all-entity tests; sensitive reasons are not persisted in
audit; subject-rights reads lack reason enforcement; and nonexistent lineage targets
return empty success instead of hidden `404`. Phase 4 has not started.

### Phase 3 acceptance — 2026-07-30

Phase 3 is **complete and independently accepted**. Final evidence: 88 PostgreSQL
tests passed with no skips at 90.67% coverage; Ruff, strict mypy, Bandit and
dependency consistency passed; fresh/base and `0005 -> 0004 -> 0005` migration
lifecycles passed; rebuilt API/database healthy; migration exited 0; live/ready
smoke returned `ok`; Trivy found zero critical vulnerabilities with exit code 0;
Gitleaks found no leaks. The independent targeted acceptance suite passed 20 tests.
Phase 4 has not started and requires a separate entry instruction.

## Authoritative phase realignment and Work Package 1 — 2026-07-30

The authoritative Education Success OS Google plan now controls phase names.
Previously accepted identity/tenancy work contributes to authoritative Phase 1/2,
and the canonical education implementation previously called local Phase 3 is
credited to authoritative Phase 2. Work Package 1 is accepted. The controlling
Google roadmap defines authoritative Phase 3 as First ERP Connector, not
intervention/case workflow; intervention is Phase 9. Phase 3 remains unimplemented
and is blocked at entry pending the approved pilot connector package. No later phase
has started.

Work Package 1 implementation adds separate Core/AI Compose profiles and networks,
bounded Core/AI resources, a credential-free internal degraded AI contract test
double, provider-neutral version-1 event envelopes, transactional outbox and
processed-event models, and additive migration `0006`. No connector, intervention,
retrieval, model router, embedding, reranking or inference implementation was added.

Final executable evidence supersedes the earlier Docker-blocked evidence. Docker
Desktop 4.83.0 (engine 29.6.2, Compose 5.3.1) ran the complete `0006 -> base ->
0006` and `0006 -> 0005 -> 0006` PostgreSQL migration lifecycle. The full
PostgreSQL-backed suite passed 97 tests with no skips at 90.91% coverage. Ruff
formatting/lint, strict mypy, Bandit, dependency consistency and diff checks passed.
The API, AI contract test double and derived PostgreSQL images built; Trivy reported
zero critical vulnerabilities for all three images with exit code 0; Gitleaks found
no leaks. Database and API containers are healthy, migration completed with exit
code 0, and live/readiness smoke returned `ok`.

Core-only startup and Core-plus-AI-test-double startup passed. The AI test double
has no database credential or host port, is attached only to the AI boundary
networks, and returns the bounded disabled response. After the AI container was
stopped, Core live/readiness remained `ok`. Work Package 1 is independently
accepted on this evidence. Authoritative Phase 2 remains incomplete, authoritative
Phase 3 remains unimplemented, and Phase 4 remains prohibited.

## Phase 2 semantic contract audit — 2026-07-29

A post-remediation contract-to-OpenAPI audit corrected three gaps:

- every mutation now exposes its enforced `Idempotency-Key` in OpenAPI;
- role-assignment revocation now requires versioned `If-Match`;
- institution deletion requests require a verified active tenant-owner membership
  approval, not only a platform-administrator reason.

The role-assignment version change is delivered in additive revision `0004`; applied
revision `0003` remains immutable. Both an existing `0003 -> 0004` upgrade and the
complete `0004 -> base -> 0004` lifecycle passed.

Superseding final evidence: 55 PostgreSQL tests passed with no skips at 90.16%
coverage; revision `0004 (head)`; Ruff, mypy, Bandit, pip-audit and secret scan
passed; the final image built; Trivy returned exit code 0 with 0 critical findings;
API/database were healthy; migration exited 0; and live/ready smoke passed. Phase 3
has not started.

## Phase 2 PostgreSQL API-runtime parity audit — 2026-07-29

The protected API was exercised through the non-superuser, non-`BYPASSRLS`
PostgreSQL application identity. Platform activation, suspension and deletion
approval now establish transaction-local tenant context before accessing
RLS-protected policy, audit, membership or role tables.

A real PostgreSQL API journey covers onboarding, activation, suspension,
reactivation and tenant-owner-approved deletion request. The SBOM gate was also corrected from obsolete `--output-file` to
supported `--outfile` in CI and the Makefile.

Superseding evidence: 56 PostgreSQL tests, no skips, 90.32% coverage; revision
`0004`; validated 91-component CycloneDX SBOM; all quality/dependency gates; final
image; Trivy exit 0 with 0 critical findings; no source leaks; healthy API/database;
migration exit 0; and successful live/ready smoke. Phase 3 has not started.

## Phase 2 persistent-replay process-boundary validation — 2026-07-29

Persistent idempotency was additionally exercised across application-instance
recreation against PostgreSQL through the non-superuser runtime role. A mutation
created by one application instance was replayed by a newly constructed instance
using the same key; the stored status and response body were returned, and a
migration-owner query confirmed that exactly one business row existed.

The complete gate set was rerun: 56 PostgreSQL tests passed with no skips at 90.32%
coverage; Ruff formatting/lint, strict mypy, Bandit, pip-audit and `pip check`
passed; both `0003 -> 0004` and `0004 -> base -> 0004` migration paths passed;
the 91-component CycloneDX SBOM validated; the rebuilt API and database were
healthy; migration exited 0; live/ready smoke passed; Trivy reported 0 critical
vulnerabilities with exit code 0; and Gitleaks found no leaks. Phase 2 remains
complete. Phase 3 has not started.

## Authoritative Phase 3 entry assessment — 2026-07-30

The next phase is **Phase 3 — First ERP Connector**. Its objective is one read-only
pilot connector with identity resolution, reconciliation, error/quarantine handling,
incremental synchronization and observable freshness. Entry is **blocked** because
there is no selected pilot ERP, approved representative source schema/mapping,
transport and credential policy, identity-resolution policy, numeric completeness,
freshness and reconciliation thresholds, or connector HLD/LLD/API/threat-model
package.

No connector source, API, migration or test was added. The conditional vertical task
list and required approval inputs are recorded in
`AUTHORITATIVE_PHASE_3_ENTRY_CRITERIA_ASSESSMENT.md`. No later phase has started.

## Authoritative Phase 2 Sprint 4 design gate — 2026-08-05

The latest local Engineering HLD and Implementation Backlog correct the earlier
roadmap interpretation: the integration framework/mock adapter and first real ERP
connector belong to authoritative Phase 2; Phase 3 is intervention workflow and
Phase 4 is the self-hosted knowledge/AI layer.

The Sprint 4 HLD, LLD, data model, API/event contract, threat model and implementation
plan now define a generated-data-only `generated_mock_v1` adapter, closed mapping and
validation contracts, tenant/RLS-protected durable jobs, transactional checkpoints,
safe quarantine/reconciliation, and the existing canonical-service/outbox boundary.
The independent design review accepts the package as a design candidate.

**Implementation is not authorized yet.** No source, test or migration was added.
Explicit approval of this exact package is required before additive revision `0007`
or connector code begins. The real connector remains Sprint 5 and blocked; Phase 3
and Phase 4 remain unimplemented.

## Authoritative Phase 2 Sprint 4 implementation evidence — 2026-08-05

The design package was explicitly approved and implemented without expanding scope.
Revision `0007` is self-contained and additive; revisions `0001`-`0006` were not
modified. The enabled adapter registry contains only `generated_mock_v1`, accepts
generated fixtures only, and has no network, filesystem or credential input.

Implemented scope includes tenant-owned/RLS-protected connector configuration,
immutable mapping versions, durable jobs, leases, batches and watermarks, safe
normalized staging, value-free validation quarantine, reconciliation manifests,
dead-letter replay controls, canonical learner observation/lineage dispatch, and
safe transactional lifecycle events. Operator APIs enforce explicit permissions,
scope, persistent idempotency, ETags, bound opaque cursors, MFA/reason replay and
hidden cross-tenant resources.

Final executable evidence: the complete PostgreSQL-backed suite passed **116 tests**
with no skips at **90.97% coverage**. Fresh `base -> 0007`, complete
`0007 -> base -> 0007`, and existing `0007 -> 0006 -> 0007` migration lifecycles
passed. Ruff format/lint, strict mypy, Bandit, `pip check`, lockfile audit and diff
checks passed. The audit identified three advisories in `cryptography 48.0.1`; the
pin and Windows/Alpine hashes were upgraded to 50.0.0 and the rerun found no known
vulnerabilities.

The API, migration, AI-contract-test-double and derived PostgreSQL images built.
Trivy reported zero critical vulnerabilities for API, AI test double and database
with exit code 0; Gitleaks found no leaks. Core-only and Core-plus-AI startup passed,
migration exited 0, database/API/AI containers became healthy, live/readiness
returned `ok`, and stopping AI left Core live/readiness `ok`.

Sprint 5 remains blocked pending the authoritative pilot ERP package. No real ERP
transport, intervention workflow or Phase 4 AI service was implemented.

### Sprint 4 independent-review disposition — 2026-08-05

The preceding evidence is **superseded as acceptance evidence** by the independent
review. Sprint 4 is **rework required**, not complete. The review found that the
initial green suite did not execute the connector transaction on PostgreSQL and
missed batch immutability, canonical-boundary and entity-coverage defects. Those
three defects, plus job-specific quarantine/cursor binding and recent-auth replay
checking, have been remediated. The current PostgreSQL-backed suite passes 116 tests
at 91.06%, including a real nine-entity connector API sync.

Remaining blockers are durable committed-batch worker recovery, functional
dead-letter replay, mapping sets, composite tenant relationships/tenant immutability,
complete append-only grants, staging cleanup and direct missing C4 security cases.
The prior image/Trivy/smoke evidence predates this remediation and must be rerun only
after these blockers close. Sprint 5, Phase 3 and Phase 4 have not started.

### Sprint 4 remediation validation candidate — 2026-08-05

All previously identified implementation blockers have been remediated in the
generated-only boundary. Revision `0007` now includes mapping sets, composite tenant
foreign keys, immutable tenant triggers and append-only runtime grants. Execution
supports `FOR UPDATE SKIP LOCKED`, committed one-batch transactions, same-job
watermark resume, generated-record dead-letter creation/replay with the original
mapping version, and terminal staging expiry cleanup. All nine approved canonical
entity types traverse the observation/lineage service.

Fresh evidence: **120 PostgreSQL-backed tests passed**, no skips, **91.23% coverage**;
`0007 -> 0006 -> 0007` and `0007 -> base -> 0007` passed; Ruff, mypy, Bandit,
`pip check` and `pip-audit` passed; all four images built; Trivy reported **0
critical** for API, database and AI test double; Gitleaks found no leaks; migration
exited 0; API/database were healthy; live/readiness returned `ok`; stopping AI left
Core healthy.

Trusted pre-`0007` SHA-256 baseline: `0001 29D75FA384C2B53820B00C125FD9748C6CA125CD451043038EABD0CC7ECF6F9E`,
`0002 4EEDCCFD9895C496E1CB4AD16AD40B7D93BBE82E87C5BDCFDA7C36A61AEF6455`,
`0003 303BAF29A9C98F82B09C5E2C615E3E354E1DE7AA17DB5CB951C9191615B1684D`,
`0004 BC6BC3BB86651D223681F7AEA366108A03FDB59D93F0434910EB665AFF5BC8C5`,
`0005 D27EE80670181F73870116F25D66B89C63A1CFF6F0F9CADC125E92379989AD39`,
`0006 DFD2DF3CC7E0B53B7DFB068D6C79F5EDE78D808B191E3B85A2FDAFB53464FC00`.

Sprint 5, intervention workflows and Phase 4 AI services remain unimplemented.
The first independent re-review correctly retained rework for missing direct C4
cases. Those findings were remediated with worker-created dead-letter/replay,
committed same-job recovery, immutable replay-input, tenant-less worker, late-arrival,
delegation-ceiling, runtime mutation/delete and connector-failure/Core-health tests.
The final independent re-review decision is **Accepted**. C4-T11 now exercises the
real late connector path and proves the current projection is not overwritten, and
the corrected C4 mappings identify committed recovery, tenant-less failure,
runtime mutation/delete, delegation-ceiling and Core-isolation tests. Authoritative
Phase 2 Sprint 4 is complete. Sprint 5 remains blocked and has not started.

## Authoritative Phase 2 Sprint 5 design gate — 2026-08-05

Sprint 5 is the **First Real ERP Connector**. A fail-closed HLD, LLD, data model,
API/event contract, threat model, implementation plan and entry-criteria assessment
have been created. No implementation, migration, external connection or credential
configuration was performed.

The referenced authoritative pilot attachment is absent from the repository and
conversation attachments available to this workspace. Vendor/product/version,
read-only transport, source inventory/schema, mappings, authority/identity rules,
credential/network policy, privacy lifecycle and numeric success thresholds are all
unresolved. The design is therefore **blocked and not approved for implementation**.
Sprint 4 generated-fixture choices cannot be promoted into real-pilot policy.

Phase 3 intervention workflows and Phase 4 AI services remain unimplemented.

Independent review decision: **Blocked, not approved for implementation.** The
review accepts the package as a fail-closed scaffold but confirms that candidate
schema, API/event and transport controls cannot be frozen without the authoritative
pilot package. Re-review is required after all pilot values and owner approvals are
supplied.

### Sprint 5 replaceable mock pilot package — 2026-08-05

Created `docs/pilot/mock/synthetic_reference_erp_v1` using generated data only. It
contains a versioned manifest and checksums, closed schemas, eight valid records,
nine negative/resilience scenarios, mock transport/identity/privacy/threshold
policies, and an editable seven-sheet pilot matrices workbook. The package uses an
in-process read-only CSV test double with no egress or credential and is explicitly
`NOT APPROVED` for production or real-connector authority.

This supports design and future automated-test preparation only. It does not satisfy
the missing real pilot package, change the independent `Blocked` decision, authorize
Sprint 5 implementation, or begin Phase 3/Phase 4.

### Sprint 5 demo-only design approval candidate — 2026-08-05

The user approved `synthetic-reference-erp-v1@1.0.0` for demo purposes only. The
Sprint 5 HLD, LLD, data model, API/event contract, threat model, implementation plan
and entry assessment are now bound to its generated schemas, mappings, exact
identity/authority rules, no-network transport, privacy lifecycle and numeric mock
thresholds. Production owner approvals remain explicitly `NOT-APPROVED`.

This changes only the demo design gate. Sprint 5 implementation and migration
`0008` have not started and require a separate explicit user approval. A real ERP
connector, intervention workflows and
Phase 4 AI remain unimplemented.

Independent re-review disposition: **Accepted for generated demo-only design.** The
reviewer verified exact scenario alignment, complete field dispositions, dual-target
enrolment mappings, checksum/validator evidence and the production boundary. Sprint
5 demo implementation still requires a separate explicit approval; production,
`0008`, intervention and Phase 4 scope remain unstarted.

## Sprint 5 generated demo implementation candidate — 2026-08-05

The approved `synthetic-reference-erp-v1@1.0.0` demo connector is implemented through
self-contained additive revision `0008`; revisions `0001`–`0007` retain their trusted
hashes. The adapter reads only the checksum-bound generated package, has no write or
network method, accepts no caller path/URL/host/credential/TLS override, and freezes
package/schema/mapping/identity/authority/threshold snapshots under forced RLS and
append-only database controls.

All nine canonical entity types are projected from eight generated source records.
The nine approved negative scenarios cover drift, prohibited attributes, duplicates,
identity ambiguity, late correction, timeout, throttling, credential rejection and
oversized input. Deterministic completeness/freshness/rejection/duplicate/
reconciliation thresholds block promotion and emit safe versioned events.

Initial evidence (superseded below): **146 PostgreSQL-backed tests passed**, no skips,
**91.36% coverage**;
C5-T01–C5-T24 have executable test nodes; `0007 → 0008 → 0007 → 0008` and complete
`head → base → head` migration lifecycles passed; Ruff, strict mypy, Bandit,
`pip check`, pip-audit and the 91-component CycloneDX SBOM passed. API, migration,
database and AI test-double images built. Trivy found **0 critical** vulnerabilities
in API, database and AI images; Gitleaks found no leaks. Migration exited 0,
database/API/AI were healthy, live/readiness returned `ok`, the package verified
inside the API image with networking disabled, and stopping AI left Core healthy.

Completion remains a candidate until independent review. Production/real ERP use,
intervention workflows and Phase 4 AI services remain unimplemented and prohibited.

### Sprint 5 independent-review remediation evidence — 2026-08-05

The first completion review required rework. All six findings are now addressed:
approved enrolment status is projected and asserted; schema-drift and transport
outages persist failed jobs and safe events, with transport attempts bounded at
three and backoff contract `[1,2,4]`; the synthetic API journey runs against the
non-bypass PostgreSQL role; event rows retain correlation metadata; PostgreSQL
enforces the 24-hour landing and seven-day quarantine maxima; and a transparent
forward checksum baseline covers revisions `0001`–`0007`.

Final candidate evidence is **148 PostgreSQL-backed tests passed**, no skips, at
**91.28% coverage**. Both `0007 → 0008 → 0007 → 0008` and `head → base → head`
lifecycles pass at `0008 (head)`. Ruff formatting/lint, strict mypy, Bandit,
`pip check`, and `pip-audit` pass; the validated CycloneDX SBOM contains 91
components. API, migration, database and AI-test-double images build. Trivy reports
zero critical vulnerabilities for all four images, Gitleaks reports no leaks,
migration exits zero, API/database are healthy, live/readiness return `ok`, Core
remains ready after AI stops, and the package verifies with Docker networking
disabled. Production enablement, a real ERP, interventions and Phase 4 remain
prohibited.

Independent re-review decision: **Accepted for the generated demo scope**. The
accepted revision `0008` checksum is recorded in the migration immutability baseline.
Authoritative Phase 2 Sprint 5 generated-demo work is complete; this does not approve
or enable production use or a real connector.

## Production First Real ERP Connector design gate — 2026-08-05

The repository was reassessed for the requested approved production package. Only the
generated demo package exists, and it explicitly records all production approvals as
`NOT-APPROVED`. A production HLD, LLD, data-model boundary, API/event boundary,
transport-extensible threat model, implementation sequence, package checklist and
entry assessment now document the fail-closed design gate. Concrete binding and
approval remain **Blocked**; no code, migration, endpoint, real connection,
intervention workflow or Phase 4 service was added.

Independent review accepted the structural documents as a fail-closed scaffold and
confirmed that concrete production design, entry and implementation remain blocked.

## Synthetic production-like operational validation — 2026-08-05

The user authorized the next synthetic-only validation milestone. A bounded harness
now provides baseline (10 complete reads), resilience (four closed failure classes)
and soak (250 complete reads, 3,000 generated records, page size five) profiles. Every
report is safe-value-only and fixes `classification` to
`generated-production-like-validation-only`, `network_egress=false` and
`production_ready=false`.

Fresh evidence: all three profiles pass; the full PostgreSQL-backed suite passes
**153 tests**, no skips, at **91.38% coverage**. Ruff, strict mypy, Bandit (no
medium/high findings), `pip check` and `pip-audit` pass. API/migration images rebuild,
Alembic remains `0008 (head)`, the resilience profile passes inside the API image
with Docker networking disabled, Core live/readiness return `ok`, and Trivy reports
zero critical API-image vulnerabilities. No API, schema, migration, credential,
network, real-source, intervention or Phase 4 capability was added.

## Authoritative Phase 3 entry reassessment — 2026-08-05

The accepted Phase 2 generated connector satisfies the authoritative roadmap's “first ERP connector or mock connector” sequencing condition. Phase 3 design entry is **GO** using generated or irreversibly anonymised examples only.

Phase 3 implementation remains **not approved** because the intervention-specific design suite and independent review do not yet exist. No intervention code, endpoint or migration was added. The real ERP remains required for pilot/production validation, and Phase 4 remains prohibited.

## Authoritative Phase 3 design candidate — 2026-08-05

The Core Intervention Workflow HLD, LLD, data model, API/event contract, threat model, implementation plan and refreshed entry assessment are complete. They cover human ownership, deterministic transitions, assignments/tasks, SLA/escalation, code/reference-only evidence/annotations, outcomes, reporting, closed case-attribute mutation, tenant/organizational scope, replay/concurrency/audit, safe notification events, complete subject-rights participation, AI-independent operation and C3-T01–C3-T40.

Status: **independently accepted design; implementation not approved**. No source, API implementation or migration was added. A real ERP remains a pilot/production dependency and Phase 4 remains prohibited.
