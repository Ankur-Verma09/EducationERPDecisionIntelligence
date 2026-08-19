# Phase 3 Implemented API

Status: In progress; not accepted  
Date: 2026-07-29  
Target contract: `PHASE_3_API_CONTRACT.md`

## Implemented

- academic-period list/create/detail/update;
- programme list/create/detail/update and version creation;
- course list/create/detail/update and version creation;
- offering list/create/detail/update;
- masked learner list/create/detail/update;
- processing restriction and resumption;
- audited protected-reference reveal with MFA, reason, and `no-store`;
- programme/offering enrolment list/create/detail and transitions;
- learner lineage read;
- reconciliation list/detail/resolve;
- subject-rights request list/create/detail;
- strict request schemas, persistent mutation idempotency, ETags, opaque cursors,
  standard errors, request IDs, tenant context, scoped permissions, MFA, audit, and
  response minimisation.

Reconciliation dismissal and subject-rights completion/export-manifest metadata are
now implemented. Public API remains intentionally absent for source
registration/observations because those belong to the Phase 4 connector contract.

Phase 3 list cursors are HMAC-signed, expire after one hour, and are bound to tenant
and collection. Subject-rights reads require `X-Access-Reason`; sensitive reasons
are retained in audit. Generic lineage covers all nine approved entities and returns
source code, source/observation versions, mapping version, authority,
observed/effective/recorded timestamps and relationship. Nonexistent targets return
hidden `404`. Export manifests are metadata-only, expire after 24 hours, and are
limited to one per subject request.

Phase 3 is independently accepted. Public source registration/ingestion remains
intentionally deferred to Phase 4.
