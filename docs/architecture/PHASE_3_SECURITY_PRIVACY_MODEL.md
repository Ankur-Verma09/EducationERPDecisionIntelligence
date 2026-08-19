# Phase 3 Security and Privacy Model

Status: Approved baseline  
Date: 2026-07-29  
Scope: Canonical Education Model

## Governing principles

1. Institution remains the legal and security tenant.
2. ERP systems remain authoritative; the canonical store is a traceable operational
   projection, not an independent source of truth.
3. Store only data required for institutional decision-support foundations.
4. Treat every learner record as sensitive and every learner as potentially a child.
5. Deny access unless an active tenant membership, permission, and resource scope all
   authorize the operation.
6. Never use production records in development, tests, examples, or demonstrations.
7. Preserve provenance and correction history; never silently rewrite source facts.
8. Phase 3 provides canonical data management only. It makes no risk, eligibility,
   disciplinary, admissions, financial, or other consequential decision.

## Lawful purpose and use limitation

The approved Phase 3 purpose is to normalize institution-authorized ERP education
records for operational data quality, future explainable analytics, and authorized
institutional workflows. Each deployment must record a jurisdiction-specific lawful
basis and controller instructions before production ingestion.

Phase 3 data must not be used for advertising, behavioral profiling, biometric
identification, automated consequential decisions, or training general-purpose
models. A missing deployment privacy configuration is a production-readiness
blocker.

## Classification

| Class | Examples | Default handling |
|---|---|---|
| Restricted learner data | learner identifiers, enrolments, cohort membership | Tenant and scope authorization; encrypted transport/storage; audited mutation and bulk/read-lineage access |
| Confidential academic structure | offerings, sections, staff assignments | Tenant authorization; scope-limited |
| Internal reference data | academic periods, programmes, courses | Tenant authorization |
| Security metadata | lineage, source keys, reconciliation state | Restricted to data stewards/integration operators; source identifiers masked in ordinary APIs |
| Prohibited | health, disability, religion, ethnicity, biometrics, precise location, disciplinary narratives, free-form notes, credentials | Reject from Phase 3 canonical payloads |

Names, personal email, phone, postal address, date of birth, gender, guardian data,
government identifiers, photographs, and demographic attributes are outside the
first-release canonical model. Authentication identity remains in Phase 2 and is not
copied into learner records.

## Approved first-release data

- generated canonical learner key;
- institution-assigned learner reference, stored encrypted or tokenized where the
  deployment supports it and masked in ordinary responses;
- optional link to an existing Phase 2 platform user when independently authorized;
- academic periods;
- programmes and programme versions;
- courses and course versions;
- course offerings/sections;
- enrolments and their effective status history;
- staff-to-offering teaching assignments referencing existing Phase 2 users;
- source systems and record lineage;
- reconciliation issues without raw source payloads.

## Prohibited attributes and payload behavior

APIs use explicit allowlists and reject unknown fields. Raw ERP payloads, arbitrary
JSON extension bags, free-form learner notes, and unclassified custom attributes are
not stored in Phase 3. New attributes require privacy classification, purpose,
retention, authorization, threat-model, schema, and migration review.

## Masking and minimisation

- Ordinary learner responses expose canonical IDs and a masked institutional
  reference only.
- Unmasked institutional references require `learner_identifier:read`, MFA, a reason,
  and an audit event.
- Source-system keys require `lineage:read` and are never returned by general learner
  endpoints.
- List responses contain no direct identifiers beyond canonical IDs and masked
  references.
- Logs, metrics, traces, error messages, cursor payloads, idempotency records, and
  audit `changes` must not contain unmasked identifiers or raw payloads.

## Retention and deletion

Conservative platform defaults:

| Record | Default | Rule |
|---|---:|---|
| Active canonical academic records | While institution contract and purpose remain active | Deployment may shorten, not silently extend |
| Superseded versions and lineage | 7 years after the associated academic period closes | Required for provenance; configurable downward when law/policy permits |
| Reconciliation issues | 2 years after resolution | No raw source payload |
| Idempotency records | 24 hours | Existing Phase 2 rule |
| Audit events | 7 years | Access controlled and immutable |

Retention is policy-driven and executed by a later approved deletion job. Phase 3
implements retention metadata and deletion eligibility, not physical erasure.
Institution deletion remains the Phase 2 governed workflow. Legal hold freezes
deletion eligibility and is deployment-configured; Phase 3 does not create a legal
hold workflow.

## Subject rights

Authorized privacy administrators can:

- locate canonical records by protected institutional reference;
- export a minimised, machine-readable subject package;
- record correction, restriction, and deletion requests;
- correct canonical projections without altering preserved source observations;
- mark records restricted from ordinary processing;
- determine deletion eligibility and record exemptions.

Exports and unmasked searches require MFA, a reason, bounded results, and audit.
Automated deletion and jurisdiction-specific response deadlines are outside Phase 3.

## Authorization matrix

New permissions are additive to Phase 2:

| Role | Read structure | Manage structure | Read learners/enrolments | Manage enrolments | Read lineage/reconcile | Unmask/export/rights |
|---|---|---|---|---|---|---|
| tenant_owner | Tenant-wide | Tenant-wide | Tenant-wide | Tenant-wide | Tenant-wide | Tenant-wide with MFA/reason |
| tenant_admin | Tenant-wide | Tenant-wide | No by default | No by default | No by default | No |
| security_admin | Metadata only | No | No | No | Audit only | No |
| auditor | Tenant-wide metadata | No | Masked, read-only | No | Read-only lineage with MFA | No |
| registrar | Tenant-wide | Tenant-wide | Tenant-wide masked | Tenant-wide | Reconcile with MFA | Unmask/export with MFA/reason; no deletion disposition |
| department_admin | Assigned department | Assigned department offerings | Assigned department masked | Assigned department | No source keys | No |
| viewer | Assigned scope | No | Aggregates only; no learner rows | No | No | No |
| platform_admin | No implicit tenant access | No | No | No | No | No |
| approved support grant | Exact approved scope only | No unless explicitly granted | Masked only | No | Diagnostic metadata only | No |

Teaching assignments do not grant API authorization in Phase 3. A future explicitly
approved faculty access policy may do so. Student and parent access is excluded.

Permissions:

- `academic_structure:read`, `academic_structure:manage`
- `learner:read`, `learner:manage`, `learner_identifier:read`
- `enrolment:read`, `enrolment:manage`
- `lineage:read`, `reconciliation:manage`
- `subject_rights:read`, `subject_rights:manage`, `subject_export:create`

## Security controls

- application authorization plus forced PostgreSQL RLS;
- tenant-consistent composite foreign keys on every relationship;
- campus/department scope checks for offerings and enrolments;
- persistent idempotency on mutations and imports of canonical observations;
- ETags on mutable aggregates;
- bounded opaque cursors;
- immutable audit for sensitive reads, mutations, exports, unmasking, lineage, and
  reconciliation;
- no bulk endpoint without an explicit limit and permission;
- no cross-tenant merge or shared learner identity graph.

## Production prerequisites

Before production data is processed, owners must configure jurisdiction, lawful
basis, retention schedule, controller/contact, subject-rights procedure, encryption
keys, backup deletion behavior, and approved ERP source registrations.
