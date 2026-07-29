# Requirements Traceability Matrix

Status values: `Identified`, `Planned`, `In progress`, `Implemented`, `Verified`,
`Deferred`, `Blocked`. No feature is complete until implementation and tests exist.

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
| INT-001 | Supplied mandate | Human-owned, auditable intervention workflow | Workflow | 8 | TBD | TBD | Planned |
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
