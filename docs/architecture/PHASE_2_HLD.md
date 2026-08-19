# Phase 2 High-Level Design

Status: Approved baseline  
Date: 2026-07-29

## Context and scope

Phase 2 adds the identity and institution control plane to the existing FastAPI
modular monolith. It does not add canonical student records, ERP ingestion, risk
analysis, AI, dashboards, notifications, or write-back.

## Components

```text
OIDC Identity Provider
        |
        | signed access token
        v
FastAPI authentication middleware
        |
        v
Identity + tenant-context resolver
        |
        v
Deny-by-default authorization service
        |
        +--> Institution API/services
        +--> Membership/role API/services
        +--> Audit service
        |
        v
Tenant-aware repositories
        |
        v
PostgreSQL constraints + forced RLS
```

## Domain modules

- `identity`: external identity mapping and authentication principal.
- `tenancy`: institution, campus, department, tenant configuration and lifecycle.
- `access`: memberships, roles, permissions, assignments and policy decisions.
- `audit`: immutable administrative/security event recording and query.

Transport, application services, domain rules, repositories, and persistence models
remain separate. API handlers cannot query SQLAlchemy directly.

## Trust boundaries

1. External clients and tokens are untrusted.
2. The OIDC issuer is trusted only after exact issuer, audience, signature, algorithm,
   time, and required-claim validation.
3. Tenant identifiers from requests are untrusted until matched to an active
   membership.
4. Authorization decisions occur in application services.
5. PostgreSQL RLS and composite constraints provide independent defence in depth.
6. Platform administration is a distinct control plane without implicit tenant-data
   access.

## Request flow

1. Correlation middleware assigns a request ID.
2. Authentication validates the bearer token and resolves the platform user.
3. Tenant context is read from the route for tenant APIs.
4. Active tenant and membership are verified.
5. Authorization service checks permission, scope, resource tenant, membership
   security epoch, and MFA assurance.
6. The service opens a transaction and applies transaction-local tenant context.
7. Repository operations execute under forced RLS.
8. Sensitive outcomes generate audit events in the same transaction where possible.
9. The standard response/error envelope is returned.

## Availability and failure behavior

- Public liveness remains independent of identity services.
- Readiness includes the database and migration revision; OIDC discovery/JWKS health
  is monitored separately to avoid making transient issuer outages restart healthy
  processes.
- Cached JWKS may be used only until its bounded expiry.
- Protected requests fail closed when token validation or tenant resolution is
  unavailable.
- Audit failure aborts sensitive mutations.

## Deployment

- OIDC and secret-manager endpoints are environment-specific.
- The API runtime uses a non-owner, non-`BYPASSRLS` database role.
- Migrations use a separately injected schema-owner credential.
- TLS terminates at an approved ingress; production database connections require TLS.
- Security logs and audit records are shipped to access-controlled immutable
  retention.

## Principal decisions

- External OIDC instead of local passwords.
- Institution is the tenant boundary.
- Explicit membership per institution; no inherited group access.
- Application authorization plus PostgreSQL forced RLS.
- Built-in roles with deny-by-default permissions.
- No user impersonation; only approved time-bound support memberships.
- Phase 2 stores no student or education-domain data.
