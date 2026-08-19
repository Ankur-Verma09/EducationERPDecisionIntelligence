# Phase 2 Threat Model

Status: Approved baseline  
Method: STRIDE-informed abuse-case review  
Date: 2026-07-29

## Assets

- Institution isolation boundary and lifecycle
- External identity links and authentication state
- Memberships, roles, permissions and scoped assignments
- OIDC configuration and JWKS trust
- Administrative audit evidence
- Support and break-glass grants
- Database credentials and tenant context

## Threat actors

- Unauthenticated internet caller
- Authenticated user in the wrong institution
- Malicious or compromised tenant administrator
- Compromised platform/support account
- Misconfigured or compromised IdP client
- Insider with database/runtime access
- Application defect that leaks pooled tenant context

## Threats and controls

| ID | Threat | Primary controls | Required tests |
|---|---|---|---|
| T2-01 | Forged/modified token | Exact issuer/audience, signature and algorithm validation | malformed, wrong issuer/audience/alg/signature |
| T2-02 | Stolen privileged token | 15-minute lifetime, MFA/recent auth, security epochs, revocation | stale epoch, expired, missing MFA |
| T2-03 | Tenant-header/path forgery | Resolve tenant only through active membership | forged header/path, missing membership |
| T2-04 | Cross-tenant IDOR | Service ownership checks, opaque-safe 404, forced RLS | guessed IDs across every CRUD path |
| T2-05 | Vertical privilege escalation | Deny-by-default permission and delegation rules | viewer/admin/owner negative matrix |
| T2-06 | Role self-escalation | Grant subset rule, owner-only owner grants, audit | self-grant and grant-above-authority |
| T2-07 | Cross-tenant FK/join leak | Composite tenant FKs and RLS | cross-tenant insert/join/update |
| T2-08 | Connection-pool context leak | `SET LOCAL`, transaction scope, clearing hooks | alternating tenant pool reuse |
| T2-09 | Last-owner lockout | Last-owner invariant and transaction locking | concurrent revoke/suspend |
| T2-10 | Duplicate mutation/replay | Idempotency key/request hash and unique constraints | same/different payload races |
| T2-11 | Support impersonation abuse | No impersonation; approved expiring membership; alerts | expiry, scope and self-extension denial |
| T2-12 | Break-glass abuse | Strong MFA, 60-minute cap, reason, alert and review | missing reason/MFA, duration limit |
| T2-13 | Audit suppression/tampering | Mutation fails if audit fails; append-only grants | audit rollback/immutability |
| T2-14 | Sensitive logging | Structured allowlist/redaction and audit minimisation | token/claim/PII log probes |
| T2-15 | JWKS poisoning/outage | HTTPS, exact issuer discovery, cache bounds, fail closed | unknown key, rollover, unavailable issuer |
| T2-16 | Mass assignment | Explicit request/response schemas | attempts to set tenant/status/roles |
| T2-17 | Enumeration | Generic auth errors, safe 404, pagination/rate limits | email, subject, tenant and ID enumeration |
| T2-18 | Institution deletion/data loss | Dual approval, cooling period, legal hold, backups | invalid transition and premature deletion |
| T2-19 | Disabled tenant/user retains access | Security epochs and live membership/tenant check | suspension/revocation immediate denial |
| T2-20 | Platform role accesses tenant data | Separate control-plane policy; no implicit membership | platform admin tenant-data negative test |

## Abuse cases

1. A tenant administrator guesses another institution's membership UUID.
2. A user changes the route tenant while retaining a valid token.
3. A department administrator assigns a tenant-owner role.
4. Two administrators concurrently revoke the last tenant owner.
5. A pooled connection retains tenant A context for tenant B.
6. A support engineer extends their own access grant.
7. A caller replays an invitation idempotency key with a different email.
8. An attacker supplies an HS256 token using the public key as an HMAC secret.
9. A revoked user presents an otherwise unexpired access token.
10. An audit storage failure occurs during a privilege mutation.

Every abuse case requires an automated negative test before Phase 2 acceptance.

## Residual risks

- Compromise of the approved IdP remains an upstream identity risk; mitigate through
  provider governance, MFA, alerts, key rotation and security epochs.
- Database superusers can bypass isolation; restrict and monitor administrative
  access and never use superuser credentials at runtime.
- Seven-year audit retention may require jurisdiction-specific adjustment before
  production; legal hold and configuration are mandatory.
- DDoS, full incident response and disaster recovery receive deeper validation in
  later phases, but basic rate/body limits remain required for Phase 2 APIs.
