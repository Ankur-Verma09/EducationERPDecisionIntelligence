# Authoritative Phase 3 — Intervention API and Event Contract

Status: Independently accepted design; implementation not approved  
Date: 2026-08-05  
Base: `/api/v1/tenants/{tenant_id}`

## Common contract

OIDC, verified tenant context, hidden `404`, standard errors, request IDs, persistent idempotency, ETags, opaque tenant/route/filter-bound cursors and `Cache-Control: no-store` reuse accepted controls. Every mutation requires `Idempotency-Key`; every mutation of an existing aggregate also requires `If-Match`. Models forbid extra fields. Limits default to 50 and are bounded 1–100.

## Permissions

`intervention:read`, `intervention:create`, `intervention:manage`, `intervention:assign`, `intervention:transition`, `intervention:evidence`, `intervention:outcome`, `intervention:report`, `intervention:export`. Assignment, reopen, cancellation, export and restricted-content access require recent MFA and a closed `reason_code` enum where specified by policy. No free-text reason exists. Permissions never replace organizational scope.

## Endpoints

| Method and path | Permission | Contract |
|---|---|---|
| `POST /intervention-cases` | create | Create generated-data case in `draft` or `open` |
| `GET /intervention-cases` | read | Opaque cursor; server-derived scope/filter; masked learner reference |
| `GET /intervention-cases/{case_id}` | read | Safe detail and ETag |
| `PATCH /intervention-cases/{case_id}` | manage | Priority only; eligible states, MFA, closed reason, ETag; SLA unchanged |
| `POST /intervention-cases/{case_id}/narrow-scope` | manage | Scope narrowing only; MFA + closed `reason_code`; fails on incompatible grants |
| `POST /intervention-cases/{case_id}/sla-policy-rebind` | manage | Active non-breached case; deadline `> now` and `>= current`; MFA + closed `reason_code` |
| `POST /intervention-cases/{case_id}/assignments` | assign | Human owner change; MFA + closed `reason_code` for reassignment |
| `POST /intervention-cases/{case_id}/transitions` | transition | Closed state/action and reason code |
| `POST /intervention-cases/{case_id}/tasks` | manage | Create bounded task |
| `GET /intervention-cases/{case_id}/tasks` | read | Bound cursor |
| `POST /intervention-tasks/{task_id}/assignments` | assign | Scope-compatible human assignee |
| `POST /intervention-tasks/{task_id}/transitions` | manage | Closed task transition |
| `POST /intervention-cases/{case_id}/evidence` | evidence | Structured metadata/reference only |
| `GET /intervention-cases/{case_id}/evidence` | read | Classification-filtered result |
| `POST /intervention-cases/{case_id}/annotations` | evidence | Closed purpose/observation codes only; no text |
| `GET /intervention-cases/{case_id}/annotations` | read | Classification and scope enforced |
| `POST /intervention-cases/{case_id}/outcomes` | outcome | Human attestation; required before resolve |
| `GET /intervention-cases/{case_id}/history` | read | State/assignment/task/outcome history; MFA for restricted metadata |
| `GET /intervention-reports/case-summary` | report | Suppressed aggregate projection plus watermark |
| `POST /intervention-cases/{case_id}/export-manifest` | export | Single learner/case, MFA + closed `reason_code`, metadata only |

Case type is immutable. Scope cannot widen or move; cancel-and-recreate is required. No bulk mutation, free-text comment/rationale, binary upload, arbitrary URL, direct notification delivery, AI endpoint or ERP write-back endpoint is approved.

## Representative generated requests

```json
{
  "learner_id": "10000000-0000-4000-8000-000000000001",
  "case_type": "engagement_support",
  "priority": "standard",
  "department_id": "20000000-0000-4000-8000-000000000001",
  "owner_user_id": "30000000-0000-4000-8000-000000000001",
  "source": {"kind": "human_referral", "reference_id": "40000000-0000-4000-8000-000000000001"}
}
```

```json
{"action":"start","reason_code":"triage_complete"}
```

```json
{
  "kind":"human_observation",
  "observation_code":"scheduled_check_in_completed",
  "effective_date":"2026-08-05",
  "confidence":"observed",
  "classification":"restricted"
}
```

Fields such as name, contact, guardian, diagnosis, disability, health, discipline, ethnicity, religion, finance, comment, rationale, notes, free-form attributes, raw ERP payload, prompt, model output or AI score return `422 prohibited_attribute`.

## Subject-rights integration

The existing subject-rights request, completion and export-manifest endpoints remain authoritative. Intervention cases are added as a required bounded domain participant: restriction propagates to ordinary reads/workers/projections/notifications; completion requires a disposition for every linked case; correction appends superseding structured rows; export includes allowlisted case/task/outcome codes only; deletion records eligibility/legal-hold/statutory-retention disposition without physical deletion. Cross-subject, incomplete-disposition, restricted-processing and legal-hold bypass attempts fail closed and are audited.

## Event envelope

Reuse `EventEnvelope`: `event_id`, `event_type`, `aggregate_id`, `tenant_id`, `occurred_at`, `schema_version="1"`, `trace_id`, `payload`. All events are transactional outbox rows.

Approved events:

- `intervention.case_created`
- `intervention.case_state_changed`
- `intervention.case_assigned`
- `intervention.task_created`
- `intervention.task_state_changed`
- `intervention.evidence_recorded`
- `intervention.outcome_recorded`
- `intervention.sla_due`
- `intervention.sla_breached`
- `intervention.owner_attention_required`
- `notification.requested`

Payloads contain tenant-safe UUIDs, closed codes, versions, due timestamps and organization IDs only. They exclude learner identifiers/display values, comment/rationale text, evidence values, source keys, contact routes, credentials, raw payloads and arbitrary extensions. `notification.requested` contains template code, authorized recipient user UUID and case UUID; channel/address resolution and delivery are deferred.

Consumers must deduplicate `event_id` with `processed_events`. Schema version changes are additive or receive a new version; unknown versions fail safely and dead-letter.

## Errors and headers

Add `state_conflict` (409), `ownership_conflict` (409), `processing_restricted` (423), `invalid_evidence` (422), `prohibited_attribute` (422), and existing precondition/idempotency/cursor/auth errors. Protected workflow responses use `Cache-Control: no-store`, `X-Request-ID`, security headers and ETag where mutable.

## Contract acceptance

OpenAPI tests must prove header requirements, closed schemas/enums, hidden resources, bounds, no prohibited fields, exact replay, ETag behavior, MFA plus closed-`reason_code` documentation, safe event payloads and absence of AI/write-back/upload endpoints.
