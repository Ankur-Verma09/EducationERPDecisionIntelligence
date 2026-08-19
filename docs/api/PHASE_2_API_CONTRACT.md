# Phase 2 API Contract

Status: Approved design baseline  
Base path: `/api/v1`  
Date: 2026-07-29

## Common contract

- Protected endpoints require `Authorization: Bearer <access-token>`.
- Tenant endpoints include `{tenant_id}` in the route. The route value is verified
  against active membership and never establishes authorization by itself.
- All responses include `X-Request-ID` and Phase 1 security headers.
- Collection endpoints use opaque cursor pagination:
  `?limit=50&cursor=<opaque>`, with `limit` between 1 and 100.
- Mutations require `Idempotency-Key` and optimistic updates require `If-Match`.
- Responses for mutable resources include `ETag`.
- Timestamps are RFC 3339 UTC; identifiers are UUIDs.
- Cross-tenant lookups return `404` without confirming existence.

Error envelope:

```json
{
  "error": {
    "code": "permission_denied",
    "message": "The operation is not permitted",
    "request_id": "uuid",
    "details": []
  }
}
```

## Authentication and self-service

### `GET /me`

Returns the authenticated user, assurance summary, and active institution
memberships. Permission: authenticated user.

### `GET /me/memberships`

Returns only the caller's active/invited/suspended memberships using pagination.

The API does not expose login, password, refresh-token, or password-recovery
endpoints; those belong to the approved OIDC provider.

## Platform institution administration

### `POST /platform/institutions`

Permission: `institution:create` with `platform_admin`.

Request:

```json
{
  "slug": "north-college",
  "legal_name": "North College",
  "display_name": "North College",
  "data_region": "approved-region",
  "initial_owner": {
    "issuer": "https://id.example/",
    "subject": "idp-subject",
    "work_email": "owner@example.edu",
    "display_name": "Tenant Owner"
  }
}
```

Creates a `pending` institution and invited owner atomically. Returns `201`.

### `GET /platform/institutions`

Permission: `institution:read` with `platform_admin`. Cursor-paginated control-plane
metadata only.

### `GET /platform/institutions/{tenant_id}`

Permission: platform `institution:read`, or same-tenant `institution:read`.

### `POST /platform/institutions/{tenant_id}/activate`

Permission: `institution:activate`; recent MFA required. Requires initial owner and
security policy. Returns updated institution.

### `POST /platform/institutions/{tenant_id}/suspend`

Permission: `institution:suspend`; recent MFA and reason required.

### `POST /platform/institutions/{tenant_id}/request-deletion`

Permission: platform administrator plus tenant-owner approval; records cooling
period/legal-hold checks. Physical deletion execution is not part of the synchronous
API.

## Tenant institution hierarchy

### `GET /tenants/{tenant_id}`

Permission: `institution:read`.

### `PATCH /tenants/{tenant_id}`

Permission: `institution:update`; `If-Match` and idempotency required. Immutable
fields such as ID, slug, status and data region cannot be mass-assigned.

### `GET|POST /tenants/{tenant_id}/campuses`

Permissions: `campus:read` or `campus:create`. POST requires idempotency.

### `GET|PATCH /tenants/{tenant_id}/campuses/{campus_id}`

Permissions: `campus:read` or `campus:update`; PATCH requires `If-Match`.

### `GET|POST /tenants/{tenant_id}/departments`

Permissions: `department:read` or `department:create`. Supports campus filter.

### `GET|PATCH /tenants/{tenant_id}/departments/{department_id}`

Permissions: `department:read` or `department:update`; department scope enforced.

## Membership administration

### `GET /tenants/{tenant_id}/memberships`

Permission: `membership:read`. Cursor pagination; filters for state and scoped
campus/department. Response excludes raw IdP tokens/claims.

### `POST /tenants/{tenant_id}/memberships`

Permission: `membership:invite`. Creates or safely replays an invitation.

```json
{
  "issuer": "https://id.example/",
  "subject": "optional-known-subject",
  "work_email": "user@example.edu",
  "display_name": "User Name"
}
```

Email alone never authorizes account linking; activation requires the verified IdP
identity.

### `GET /tenants/{tenant_id}/memberships/{membership_id}`

Permission: `membership:read`; cross-tenant IDs return `404`.

### `POST /tenants/{tenant_id}/memberships/{membership_id}/suspend`

Permission: `membership:update`; reason and recent MFA required for privileged
memberships.

### `POST /tenants/{tenant_id}/memberships/{membership_id}/activate`

Permission: `membership:update`; invalid transitions return `409`.

### `POST /tenants/{tenant_id}/memberships/{membership_id}/revoke`

Permission: `membership:revoke`; last-owner and self-escalation constraints apply.

## Roles and assignments

### `GET /tenants/{tenant_id}/roles`

Permission: `role:read`. Returns built-in role and permission metadata.

### `GET /tenants/{tenant_id}/memberships/{membership_id}/role-assignments`

Permission: `role:read`.

### `POST /tenants/{tenant_id}/memberships/{membership_id}/role-assignments`

Permission: `role:assign`; idempotency and delegation rules apply.

```json
{
  "role": "department_admin",
  "campus_id": "uuid",
  "department_id": "uuid",
  "expires_at": null
}
```

### `DELETE /tenants/{tenant_id}/memberships/{membership_id}/role-assignments/{assignment_id}`

Permission: `role:revoke`; `If-Match` required. Returns `204`.

## Security policy

### `GET /tenants/{tenant_id}/security-policy`

Permission: `security_policy:read`.

### `PATCH /tenants/{tenant_id}/security-policy`

Permission: `security_policy:update`; recent MFA, `If-Match`, and idempotency
required. Tenant policy cannot weaken platform minimums.

## Audit

### `GET /tenants/{tenant_id}/audit-events`

Permission: `audit:read`; MFA required. Cursor pagination with time, action, actor,
target, and outcome filters. Access is itself audited.

Audit events are immutable; no create/update/delete API is exposed.

## Support access

### `POST /tenants/{tenant_id}/support-access-grants`

Creates a pending grant with reason, ticket, requested scope, start and expiry.

### `POST /tenants/{tenant_id}/support-access-grants/{grant_id}/approve`

Permission: `support_access:approve`; tenant-owner recent MFA required.

### `POST /tenants/{tenant_id}/support-access-grants/{grant_id}/revoke`

Tenant owner/security administrator may revoke. Support users cannot approve, extend,
or broaden their own grants.

## Status codes

- `200/201/204` success
- `400` malformed request
- `401` missing/invalid authentication
- `403` known authenticated principal lacks safely discloseable permission
- `404` absent or tenant-hidden resource
- `409` state/idempotency/uniqueness conflict
- `412` stale ETag
- `422` validated input error
- `428` missing required precondition
- `429` rate limit
- `503` required dependency unavailable

## Contract test requirements

Every endpoint requires positive, authentication, permission, tenant-isolation,
invalid-state, mass-assignment, pagination, idempotency/precondition where relevant,
and audit tests before being marked implemented.
