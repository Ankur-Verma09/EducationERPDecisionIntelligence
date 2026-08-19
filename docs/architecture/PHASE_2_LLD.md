# Phase 2 Low-Level Design

Status: Approved baseline  
Date: 2026-07-29

## Proposed package layout

```text
src/education_erp/
├── identity/
│   ├── domain.py
│   ├── oidc.py
│   ├── principal.py
│   └── service.py
├── tenancy/
│   ├── domain.py
│   ├── repository.py
│   └── service.py
├── access/
│   ├── permissions.py
│   ├── policy.py
│   ├── repository.py
│   └── service.py
├── audit/
│   ├── domain.py
│   ├── repository.py
│   └── service.py
├── api/
│   ├── dependencies.py
│   ├── institutions.py
│   ├── memberships.py
│   ├── roles.py
│   └── audit.py
└── persistence/
    ├── base.py
    ├── models.py
    ├── repositories.py
    └── tenant_context.py
```

## Authentication principal

```text
AuthenticatedPrincipal
- user_id: UUID
- issuer: str
- subject: str
- token_id: str | None
- issued_at: datetime
- expires_at: datetime
- assurance: set[str]
- security_epoch: int
```

Authentication verifies the token before loading the local user. Disabled users and
tokens issued before `user.security_epoch_changed_at` are rejected.

## Tenant context

```text
TenantContext
- tenant_id: UUID
- membership_id: UUID
- user_id: UUID
- role_ids: tuple[UUID, ...]
- permission_names: frozenset[str]
- campus_ids: frozenset[UUID]
- department_ids: frozenset[UUID]
- assurance: frozenset[str]
```

Only an API dependency/service may construct this object. Handlers never construct
tenant context from caller input.

## Authorization algorithm

```text
authorize(principal, tenant_id, permission, resource_scope):
    require active user
    require active tenant
    load active membership for principal.user_id + tenant_id
    require token issued after user/membership/tenant security epochs
    union permissions from active role assignments
    require requested permission
    require campus/department scope contains resource scope
    require privileged assurance/recent MFA where policy demands
    return immutable TenantContext
```

Authorization is deny-by-default. Platform permissions and tenant permissions are
evaluated by separate policy functions.

## Persistence transaction

Every tenant service operation:

1. authorizes before opening repository work;
2. begins a database transaction;
3. executes `SET LOCAL app.tenant_id = :tenant_id`;
4. optionally sets safe actor/request metadata for audit triggers;
5. performs repository operations;
6. writes required application audit events;
7. commits atomically.

Connection checkout/return hooks clear tenant-related session state defensively.
Tests prove a connection reused by tenant B cannot observe tenant A.

## Role assignment constraints

- Built-in role names are globally stable.
- Assignment belongs to the same tenant as membership.
- Campus/department scope belongs to the assignment tenant.
- Department scope implies its parent campus.
- Only `tenant_owner` may grant/revoke `tenant_owner`.
- `tenant_admin` cannot grant `tenant_owner`, `security_admin`, or permissions it
  lacks with delegation authority.
- The last active tenant owner cannot be revoked or suspended.
- Platform roles cannot be assigned through tenant endpoints.

## Lifecycle transitions

Institution:

```text
pending -> active
active -> suspended
suspended -> active
active|suspended -> deletion_pending
deletion_pending -> active        # cancellation before execution
deletion_pending -> deleted
```

Membership:

```text
invited -> active
invited -> revoked
active -> suspended
suspended -> active
active|suspended -> revoked
```

Invalid transitions return `409 state_conflict`.

## Idempotency and concurrency

- Institution creation, membership invitation, role assignment, and lifecycle
  mutation require `Idempotency-Key`.
- Keys are scoped to actor, tenant/control-plane scope, method, and canonical route.
- Reusing a key with a different request hash returns `409 idempotency_conflict`.
- Mutations use optimistic version columns and `If-Match` ETags.
- Stale versions return `412 precondition_failed`.
- Unique constraints prevent duplicate identity links, memberships, slugs, and role
  assignments under races.

## API errors

The Phase 1 error envelope remains canonical. Additional codes:

```text
authentication_required
invalid_token
tenant_context_required
membership_inactive
permission_denied
scope_denied
mfa_required
recent_authentication_required
state_conflict
idempotency_conflict
precondition_required
precondition_failed
resource_not_found
```

Cross-tenant resource lookup returns `404 resource_not_found` to avoid confirming
resource existence. Authentication failures return `401`; authorization failures
return `403` only when existence disclosure is safe.

## Audit behavior

Sensitive mutation and its audit event share one transaction. Audit records are
append-only: application roles receive `INSERT` and approved filtered `SELECT`, never
`UPDATE` or `DELETE`. Export is permissioned, rate-limited, and audited.

## Test design

- Unit: token claims, permissions, delegation, scope, transitions, retention and
  idempotency rules.
- Integration: constraints, forced RLS, two-tenant CRUD, joins, pool reuse, audit
  atomicity, races and migration cycle.
- API: OIDC failure matrix, roles, pagination, idempotency, ETags and standard errors.
- Security: IDOR, horizontal/vertical escalation, forged tenant headers, algorithm
  confusion, unknown `kid`, stale tokens and support-access expiry.
- E2E: create tenant, activate owner, invite admin, assign role, verify isolation,
  suspend membership and prove immediate denial.
