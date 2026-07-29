# API Implementation Status

Phase 1 implements the operational health API. Runtime verification remains blocked
until the declared packages can be downloaded.

| API area | Target phase | Status | Notes |
|---|---:|---|---|
| Liveness/readiness | 1 | Remediated; verification blocked | `GET /api/v1/health/live` and migration-aware `/ready`; see `docs/api/HEALTH_API.md` |
| Identity/tenant administration | 2 | Planned | Requires identity and tenant decisions |
| Canonical education resources | 3 | Planned | Requires data model |
| Connector/sync status | 4 | Planned | Requires connector contract |
| Validation/data quality | 5 | Planned | Requires mapping and quarantine model |
| Risk scoring/explanations | 6 | Planned | Deterministic rules first |
| Knowledge/AI explanation | 7 | Planned | Grounded, authorised retrieval only |
| Interventions | 8 | Planned | Workflow and approval policy required |
| Dashboard/reporting | 9 | Planned | Backend permissions mandatory |
| Notifications/write-back | 10 | Planned | Restricted credentials and confirmation |

Every endpoint must eventually be linked to OpenAPI, authorisation rules, requirement
IDs, implementation files, and positive/negative/tenant-isolation tests.

Phase 1 has no collection or business endpoints, so pagination, authentication,
authorisation, idempotency, and tenant isolation are not applicable to its two
read-only operational endpoints. These requirements are not considered completed
globally.
