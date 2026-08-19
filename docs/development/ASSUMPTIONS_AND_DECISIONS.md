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
| DEC-018 | Do not infer Phase 2 tenant or identity boundaries from example entities and roles | These choices define security, legal data boundaries, database constraints, and authentication trust | Accepted |
| DEC-019 | Institution is the legal/security tenant; campus and department are scopes within it | Establish one durable isolation key and prevent inherited cross-institution access | Accepted |
| DEC-020 | Use external OIDC/JWT bearer validation; store no local passwords or refresh tokens | Keep authentication assurance external while API trust remains explicit | Accepted |
| DEC-021 | Users may hold explicit memberships in multiple institutions, with one verified tenant context per request | Support legitimate access without ambient cross-tenant authority | Accepted |
| DEC-022 | Use deny-by-default application authorization plus composite tenant constraints and forced PostgreSQL RLS | Independent controls reduce IDOR and repository-defect blast radius | Accepted |
| DEC-023 | Platform roles grant no implicit tenant-data access; user impersonation is prohibited | Separate control-plane authority and preserve attribution | Accepted |
| DEC-024 | Privileged actions require MFA/recent authentication; support access is approved, scoped and expiring | Reduce stolen-token and support-access abuse | Accepted |
| DEC-025 | Phase 2 stores identity/admin data only and excludes child users and education records | Apply data minimisation until later privacy/data phases | Accepted |
| DEC-026 | Migration ownership and application runtime use separate PostgreSQL roles; the runtime role is `NOSUPERUSER NOBYPASSRLS` | PostgreSQL superusers and `BYPASSRLS` roles bypass forced RLS, invalidating tenant isolation | Accepted |
| DEC-027 | Mutations persist actor-and-concrete-route idempotency for 24-hour replay | Exact replay must survive requests/workers and conflicting reuse must fail closed | Accepted |
| DEC-028 | Collection cursors encode and validate a stable UUID boundary | Clients must not depend on raw ordering fields or malformed traversal state | Accepted |
| DEC-029 | Platform-create idempotency may initially have no tenant and remains actor/route/key scoped | The tenant does not exist until atomic institution creation completes | Accepted |
| DEC-030 | Preserve applied `0003` and deliver role-revocation concurrency as additive revision `0004` | Editing an applied migration breaks existing-database upgrades and rollback fidelity | Accepted |
| DEC-031 | Platform routes establish tenant context before touching tenant-owned RLS tables | Platform authorization does not bypass PostgreSQL RLS and must not require privileged runtime credentials | Accepted |
| DEC-032 | Do not infer the Phase 3 canonical education schema or student-data boundaries from the mandate | Entity semantics, child-data duties, lineage, retention, ERP authority, and education-record authorization are high-consequence and irreversible after ingestion | Accepted |
| DEC-033 | Treat every Phase 3 learner as potentially a child and store only a tenant-local generated key plus protected institutional reference | Conservative minimisation avoids unnecessary identity/demographic exposure | Accepted |
| DEC-034 | Exclude demographics, contact, guardian, grades, attendance, finance, health, discipline, biometrics, government identifiers and free-form notes from Phase 3 | These fields lack an approved first-release purpose and materially increase privacy risk | Accepted |
| DEC-035 | ERP authority is registered per tenant and entity type; recency alone never overrides higher authority | Preserve system-of-record ownership and prevent silent corruption | Accepted |
| DEC-036 | Preserve immutable normalized observations and concrete lineage without retaining raw ERP payloads | Provide provenance while minimizing sensitive source data | Accepted |
| DEC-037 | Use effective-dated versions, explicit supersession and reconciliation; prohibit automatic learner merge | Preserve temporal truth and require human control for ambiguous identity changes | Accepted |
| DEC-038 | Phase 3 education access uses explicit permissions and organizational scopes; platform roles and teaching assignments grant no implicit record access | Prevent vertical escalation and accidental authorization coupling | Accepted |
| DEC-039 | Phase 3 records retention metadata and subject-rights workflow state but defers physical deletion and downloadable export artifacts | Deletion/backups/object storage require later operational designs | Accepted |
| DEC-040 | Deliver Phase 3 schema only in additive revision `0005`; never modify `0001`–`0004` | Preserve deployed Phase 2 upgrade and rollback fidelity | Accepted |
| DEC-041 | Protected learner-reference reveal is an audited sensitive read, not an idempotently persisted mutation response | Persisting an unmasked identifier in replay storage would violate minimisation | Accepted |
| DEC-042 | Use tenant-bound fingerprints for uniqueness/search while masking institutional references in ordinary API responses | Prevent direct-identifier enumeration and accidental disclosure | Accepted |
| DEC-043 | Keep Phase 3 in progress when executable gates pass but approved lineage, temporal, subject-rights, or threat coverage is incomplete | Passing infrastructure gates cannot substitute for required functionality/security controls | Accepted |
| DEC-044 | The authoritative Education Success OS Google plan controls phase naming; previously accepted canonical Phase 3 work is credited to authoritative Phase 2 | Prevent local governance from claiming completion of a differently defined phase | Accepted |
| DEC-045 | Authoritative Phase 3 is the intervention/case workflow and remains unimplemented | Superseded after direct verification of the controlling Google roadmap | Superseded by DEC-052 |
| DEC-046 | Add Core/AI isolation contracts and a credential-free degraded test double without implementing inference | Prove failure isolation before Phase 4 while respecting the phase boundary | Accepted |
| DEC-047 | Use additive revision `0006` for broker-neutral outbox and processed-event foundations; do not modify `0001`-`0005` | Preserve migration immutability and enable later connector/workflow event propagation | Accepted |
| DEC-048 | Core never reads AI configuration and the AI profile receives no Core database credential | Enforce independent deployment and prohibit direct AI access to Core schemas | Accepted |
| DEC-049 | Build the PostgreSQL initialization script into a derived image and compile `gosu` 1.17 with Go 1.25.7 | Avoid unreliable Windows bind-mount startup and remove the upstream binary's critical Go TLS vulnerability while preserving PostgreSQL entrypoint behavior | Accepted |
| DEC-050 | Use explicit non-internal `core_edge` and localhost-only `database_admin` networks while retaining internal data and AI boundaries | Permit intended host smoke/test access without making the AI or Core data planes externally routable | Accepted |
| DEC-051 | Do not infer the first ERP, source schema, transport, identity-match policy, raw-data treatment or acceptance thresholds | These define external trust boundaries and canonical correctness; guessing them can leak tenant data or silently corrupt authoritative records | Accepted |
| DEC-052 | The controlling Google roadmap defines authoritative Phase 3 as First ERP Connector and Phase 9 as Intervention Hub | Correct the earlier inferred phase label using the authoritative source | Superseded by DEC-053 after reviewing the latest local Engineering HLD and Implementation Backlog |
| DEC-053 | The latest local Engineering HLD and Implementation Backlog control sequencing: Phase 2 includes Sprint 4 integration framework/mock and Sprint 5 first real connector; Phase 3 is intervention and Phase 4 is self-hosted AI | Use the most specific current engineering sequence and prevent connector work being mislabeled as a later phase | Accepted |
| DEC-054 | Sprint 4 enables only `generated_mock_v1`, generated data and no external transport or credential; real ERP work requires a separate Sprint 5 design and approval | Permit safe framework validation without inventing pilot trust, schema or numeric decisions | Accepted |
| DEC-055 | Revision `0007` database-disables credential-reference rows and permits only `generated_mock_v1`; canonical updates traverse the accepted observation service | Enforce the Sprint 4 boundary below application configuration and preserve authority/lineage semantics | Accepted |
| DEC-056 | Sprint 5 may not infer a vendor, transport, schema, mapping, identity rule, credential/network policy, privacy lifecycle or numeric threshold when the referenced pilot package is absent | Real-source choices are security, privacy and correctness decisions; Sprint 4 fixture defaults are non-authoritative | Accepted |
| DEC-057 | Sprint 5 design remains blocked until product, ERP/source, privacy and security owners approve a versioned pilot package; implementation additionally requires explicit user approval | Separate evidence-based design approval from implementation authority | Accepted |
| DEC-058 | A replaceable `synthetic_reference_erp_v1` package may exercise Sprint 5 schemas, mappings and failure cases, but every value is mock-only and cannot satisfy real-pilot approval | Enable safe progress with generated data without laundering mock assumptions into production authority | Accepted |
| DEC-059 | The user approval dated 2026-08-05 authorizes `synthetic-reference-erp-v1@1.0.0` only as the concrete Sprint 5 demo design authority; production product, source, privacy and security approvals remain unmet | Permit deterministic generated-data demonstration while preserving a hard production boundary and separate implementation gate | Accepted |
| DEC-060 | Sprint 5 implementation resolves the approved package only from the repository or `/app/demo-package`; requests and environment variables cannot supply a path, host, URL or credential | Make network, SSRF, local-file and confused-deputy surfaces absent by construction | Accepted |
| DEC-061 | The application compiles the approved manifest SHA-256 and additionally verifies every declared file checksum and demo/production approval flag | Prevent a substituted manifest from becoming trusted merely by refreshing its own checksums | Accepted |
| DEC-062 | Revision `0008` permits only the Sprint 4 mock and Sprint 5 synthetic demo kinds, and makes source-schema/transport evidence tenant-scoped, forced-RLS and append-only | Enforce the demo-only boundary below request validation while preserving `0001`–`0007` immutability | Accepted |
| DEC-063 | Synthetic transport faults use three deterministic attempts with the approved `[1,2,4]` backoff contract but no wall-clock sleep in the in-process test double; terminal failure is persisted transactionally | Prove bounded retry and failure isolation without slowing tests or implying a production transport | Accepted |
| DEC-064 | The 2026-08-05 SHA-256 list is the forward immutability baseline for `0001`–`0007`; absence of an earlier trusted `0007` hash is disclosed rather than inferred | Preserve auditable evidence without overstating historical proof for the formerly untracked revision | Accepted |
| DEC-065 | A production connector design cannot reuse or promote `synthetic-reference-erp-v1@1.0.0`; every vendor, transport, schema, policy, threshold and owner approval must come from a separate checksum-bound production authority package | The demo manifest explicitly denies production authority, and invented defaults would create security, privacy and correctness risk | Accepted |
| DEC-066 | The production design remains blocked while structural boundaries and package requirements may be documented | Preserve useful design progress without representing missing source-owner decisions as approved | Accepted |
| DEC-067 | `synthetic-reference-erp-v1@1.0.0` may be used for production-like operational validation only when reports always state generated-only, no-network and `production_ready=false` | Permit repeatable workload and resilience learning without converting fictional data, mappings or thresholds into production authority | Accepted |
| DEC-068 | The authoritative Phase 2 “first ERP connector or mock connector” exit permits the accepted generated connector to satisfy Phase 3 design sequencing, but not real-pilot or production approval | Separate provider-neutral workflow progress from unavailable production-source authority | Accepted |
| DEC-069 | Phase 3 implementation requires an intervention-specific design suite, independent review and explicit approval; historical `PHASE_3_*` canonical artifacts remain Phase 2 evidence | Prevent phase-name collision from authorizing the wrong scope | Accepted |
| DEC-071 | Authoritative Phase 3 is deterministic and human-owned; job title, AI output and escalation never grant authority or silently replace the accountable owner | Preserve human accountability and AI-independent Core operation | Accepted for design |
| DEC-072 | Evidence/annotations use closed codes and canonical references; free text, binary upload, URLs, raw ERP payloads and arbitrary JSON are excluded | Preserve DEC-034 and minimise child-data/exfiltration surfaces deterministically | Accepted for design |
| DEC-073 | SLA policy/history is immutable; escalation emits an alert/proposal while consequential ownership/state changes require an authorized human | Reproducible time behavior without automated consequence escalation | Accepted for design |
| DEC-074 | Future migration `0009` is additive and self-contained and cannot modify `0001`–`0008`; it requires explicit implementation approval | Preserve migration immutability and phase gate | Accepted for design |
| DEC-056 | Upgrade the pinned `cryptography` dependency from 48.0.1 to 50.0.0 with verified Windows and Alpine hashes | Close PYSEC-2026-3552, PYSEC-2026-3553 and PYSEC-2026-3554 without weakening hashed installs | Accepted |

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

## Phase 2 entry-criteria disposition

Phase 2 authorization does not resolve its missing security inputs. Tenant boundary,
tenant hierarchy, identity provider/protocol, MFA, role-permission matrix,
multi-tenant membership, privacy/compliance baseline, threat model, and deployment
trust boundaries remain unapproved. They cannot be replaced with implementation
assumptions without risking cross-tenant exposure or an incompatible identity
architecture. Phase 2 implementation is therefore blocked at entry.

### Phase 2 approval update

The user subsequently authorized and approved a conservative Phase 2 security model.
DEC-019 through DEC-025 supersede the unresolved design questions for Phase 2 scope.
Environment-specific IdP, region and secret references remain required deployment
configuration and must fail closed when absent.

## Phase 3 entry-criteria disposition

The instruction to execute the next approved phase confirms sequence but does not
approve an education-domain schema, privacy policy, authorization matrix, source
lineage semantics, ERP conflict policy, or API contract. Phase 3 therefore remains
blocked at entry under DEC-032. The required inputs and conditional implementation
tasks are recorded in `PHASE_3_ENTRY_CRITERIA_ASSESSMENT.md`.

### Phase 3 approval update

The user subsequently authorized definition and approval of the conservative Phase 3
baseline. DEC-033 through DEC-039, the approved architecture/privacy/schema/threat/API
artifacts, and the independent design review resolve the design-entry questions.
Deployment-specific jurisdiction, lawful basis, retention shortening, legal holds,
encryption keys, and controller procedures remain production prerequisites rather
than implementation blockers for the approved provider-neutral model.

### Phase 3 remediation decisions

- DEC-041: Alembic revision `0005` owns explicit schema definitions and must never
  import mutable ORM metadata.
- DEC-042: One generic lineage contract serves the nine approved entity types through
  an explicit closed entity-to-model registry; unknown entity types fail hidden.
- DEC-043: Connector-facing ingestion remains Phase 4 scope. Phase 3 nevertheless
  supplies the internal transaction service that records observations and lineage,
  applies authority/precedence/equivalence/late-arrival rules, invokes projection
  callbacks, and creates reconciliation issues.
- DEC-044: P3-T01–P3-T26 acceptance requires executable test-node traceability in
  addition to the underlying API, unit, security and PostgreSQL control tests.
