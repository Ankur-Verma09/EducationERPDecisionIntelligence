# Phase 2 Security Model

Status: Approved project baseline  
Approved by: user execution authority  
Date: 2026-07-29  
Scope: Phase 2 — Identity, Institution, and Multi-Tenancy

## Security objectives

1. Deny access unless identity, tenant context, membership, and permission are valid.
2. Prevent horizontal and vertical privilege escalation.
3. Enforce tenant isolation in both application code and PostgreSQL.
4. Keep platform administration separate from tenant administration.
5. Make sensitive administration attributable and tamper-evident.
6. Minimise identity data and avoid storing student education records in Phase 2.

## Legal tenant boundary and hierarchy

The legal and security tenant is an **institution**. Every tenant-owned record carries
an immutable `tenant_id` equal to the owning institution identifier.

Hierarchy:

```text
Platform
└── Institution (tenant/legal isolation boundary)
    ├── Campus
    │   └── Department
    └── Tenant configuration
```

An institution group is not a tenant parent and receives no implicit access to member
institutions. Cross-institution groups may be represented later as explicit
relationships, but access still requires a separate membership in every institution.
Campus and department are authorization scopes inside one tenant; they never weaken
the institution boundary.

## User and membership model

- A user is a platform identity linked to one external IdP subject.
- A user may hold memberships in multiple institutions.
- Every request to a tenant API carries exactly one tenant context.
- Tenant context is selected explicitly and must match an active membership.
- Tenant identifiers supplied in paths, bodies, queries, or headers are never trusted
  without comparison to the verified request context.
- Memberships have `invited`, `active`, `suspended`, or `revoked` state.
- Suspension/revocation takes effect on the next authorization check and invalidates
  cached authorization state.
- A user cannot grant a role or scope they do not possess with delegation authority.
- Role assignments are tenant-specific and may optionally be narrowed to campus or
  department scope.

## Identity provider and authentication protocol

Phase 2 uses an external OpenID Connect provider:

- Authorization Code Flow with PKCE for interactive clients.
- OAuth 2.0 bearer access tokens for the API.
- The API does not accept passwords and does not implement password recovery.
- The API validates signed JWT access tokens using issuer discovery and JWKS.
- Accepted algorithms are explicitly allowlisted; `none` and symmetric algorithms
  are rejected.
- Issuer and audience are exact environment configuration values.
- Token subject and issuer form the stable external identity key.
- Machine-to-machine client credentials and SAML federation are deferred until a
  concrete connector or enterprise federation requirement is approved.

## Token and session lifecycle

- Access token maximum lifetime: 15 minutes.
- Clock skew allowance: at most 60 seconds.
- Required claims: `iss`, `sub`, `aud`, `exp`, `iat`, and unique token identifier
  (`jti`) where the provider supports it.
- Tokens issued before a user, membership, or tenant security epoch are rejected.
- Refresh tokens remain with the IdP or an approved confidential frontend/BFF and
  are never accepted by the API.
- Browser sessions use secure, HTTP-only, same-site cookies at the IdP/BFF boundary;
  the Phase 2 API remains bearer-token based.
- Signing keys are refreshed from JWKS with bounded caching and safe rollover.
- If issuer metadata/JWKS cannot be validated, protected APIs fail closed.

## MFA policy

MFA is mandatory for:

- platform administrators;
- tenant owners and tenant administrators;
- security administrators;
- auditors accessing sensitive audit detail;
- support-access approvers and support engineers receiving temporary access.

Tokens for privileged operations must contain an approved `acr` or `amr` assurance
claim. Destructive or privilege-changing operations require recent MFA, no older than
five minutes. Other institution users follow the institution's policy, with MFA
strongly recommended and configurable as mandatory.

## Roles and permissions

Built-in roles are immutable templates. Custom roles may be introduced later only
after permission-combination and escalation analysis.

| Role | Principal permissions |
|---|---|
| `platform_admin` | Create/suspend institutions; assign platform support access; no implicit tenant business-data access |
| `tenant_owner` | Manage institution lifecycle request, tenant admins, security policy, campuses and departments |
| `tenant_admin` | Manage institution profile, campuses, departments, users, memberships and non-owner roles |
| `security_admin` | Manage security policy, revoke memberships/sessions, view security audit events |
| `auditor` | Read institution configuration, memberships and audit events; no mutations |
| `registrar` | Read institution hierarchy and memberships needed for administration; no role/security changes |
| `department_admin` | Read institution/campus and administer users limited to assigned department scope |
| `viewer` | Read own profile, memberships, and non-sensitive institution directory data |

Permission names use `resource:action`, including:

```text
institution:create, institution:read, institution:update,
institution:suspend, institution:activate,
campus:create, campus:read, campus:update,
department:create, department:read, department:update,
membership:invite, membership:read, membership:update, membership:revoke,
role:read, role:assign, role:revoke,
security_policy:read, security_policy:update,
audit:read, support_access:approve
```

All unspecified actions are denied.

## Platform administration and support access

- `platform_admin` is a separate platform role and grants no automatic tenant-data
  access.
- User impersonation and token minting as another user are prohibited.
- Support access is an explicit, time-limited tenant membership with a ticket/reason,
  requested scope, approver, start, expiry, and immutable audit trail.
- Tenant-owner approval is required unless an emergency break-glass procedure is
  invoked.
- Break-glass requires strong MFA, a reason, a maximum 60-minute duration, immediate
  security alerting, and post-event review.
- Support access cannot assign roles, alter audit records, or extend itself.

## Institution lifecycle

States:

```text
pending -> active -> suspended -> deletion_pending -> deleted
```

- Only platform administrators create an institution.
- Activation requires an initial verified tenant owner and security policy.
- Suspension blocks tenant API access but preserves audit and recovery data.
- Deletion requires dual approval, a configurable cooling-off period of at least 30
  days, export/legal-hold checks, and a documented deletion job.
- Institution identifiers and slugs are never reused.
- Deleted institutions retain only legally required tombstone and audit metadata.

## Privacy, residency, retention, and child data

- Phase 2 stores identity and administrative data only; no student academic, fee,
  attendance, health, disciplinary, or risk data.
- Store display name, work email, IdP identifiers, membership, role/scope, security
  state, and audit metadata only when necessary.
- Date of birth, home address, personal phone, government identifier, biometrics, and
  student/child records are prohibited in Phase 2.
- Production data resides in the institution's configured approved region. Cross-
  region replication or support access requires explicit approval.
- Active user/membership data is retained while required for service and contractual
  obligations.
- Revoked identity profile data is deleted or irreversibly de-identified within 30
  days unless legal hold or a documented statutory requirement applies.
- Security audit events are retained for seven years by default, configurable upward
  for jurisdictional requirements. Audit payloads remain minimised.
- Legal hold overrides deletion and is itself audited.
- Child users are not supported in Phase 2. Student/parent identities require a
  separate privacy and consent approval before enablement.

## PostgreSQL isolation policy

- Every tenant-owned table has non-null `tenant_id`.
- Primary/unique keys include `tenant_id` where uniqueness is tenant-scoped.
- Foreign keys include `tenant_id` to prevent cross-tenant relationships.
- PostgreSQL Row-Level Security is enabled and forced on every tenant-owned table.
- Policies compare `tenant_id` to transaction-local
  `current_setting('app.tenant_id', true)`.
- The application sets tenant context inside each transaction after authorization.
- Missing, invalid, or empty tenant context returns no rows and prevents writes.
- The runtime database role cannot bypass RLS, own tables, create schemas, or alter
  policies.
- A separate migration role owns schema objects. Credentials are not shared.
- Platform control-plane operations use narrowly scoped audited functions or a
  separate control-plane repository; they do not use a general `BYPASSRLS` runtime
  connection.
- Integration tests must use at least two tenants and attempt guessed identifiers,
  joins, writes, updates, deletes, counts, and transaction/pool context reuse.

## Secrets and key management

- Secrets are stored in the deployment secret manager, never source, images, logs,
  environment examples, database rows, or client bundles.
- Environment variables may contain secret references or injected values at runtime;
  production fails closed when approved secret injection is absent.
- OIDC issuer/audience are configuration, not secrets.
- Private signing keys remain with the IdP. The API consumes public JWKS only.
- Database credentials are separate for migrations and runtime.
- Credentials are scoped per environment, rotated at least every 90 days and
  immediately after suspected disclosure.
- Secret access is least-privilege, logged, and unavailable to application users.
- Key rotation supports overlap so old tokens expire naturally without accepting
  untrusted keys.

## Audit requirements

Audit events are append-only and include event ID, timestamp, actor identity, tenant,
action, target type/ID, outcome, request ID, source IP classification, authentication
assurance, reason/ticket where required, and safe structured changes. Tokens, secrets,
raw headers, and unnecessary personal data are prohibited.

Required events include institution lifecycle, membership invitation/state changes,
role assignment/revocation, security-policy changes, access denial for sensitive
operations, support/break-glass access, and audit export.

## Security acceptance gates

- Authentication positive, malformed, expired, wrong issuer/audience, wrong
  algorithm, missing-claim, unknown-key, and key-rollover tests pass.
- Horizontal and vertical privilege-escalation tests pass.
- Cross-tenant list/get/create/update/delete and guessed-ID tests pass at application
  and PostgreSQL RLS layers.
- Missing tenant context fails closed, including after connection-pool reuse.
- MFA/recent-auth checks pass for privileged operations.
- Audit completeness and secret/PII minimisation tests pass.
- No unresolved critical security, tenant-isolation, correctness, or data-loss issue.
