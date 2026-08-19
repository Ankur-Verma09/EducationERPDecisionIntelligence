# Security Checklist

Legend: `[ ]` pending, `[x]` addressed in the Phase 0 documentation baseline.

## Governance and privacy

- [ ] Complete threat model and privacy impact assessment.
- [ ] Classify data and document allowed purposes, lawful basis/consent, residency,
  retention, deletion, and subject-request processes.
- [ ] Define child/student data protections and prohibited risk features.
- [ ] Assign security, privacy, incident, and operational owners.
- [x] Establish data minimisation and ERP-authority principles.

## Identity and tenancy

- [x] Approve tenant boundary and hierarchy.
- [ ] Integrate an approved IdP; require MFA for privileged roles.
- [ ] Enforce server-side RBAC/ABAC and deny by default.
- [ ] Enforce tenant ownership in application and persistence layers.
- [ ] Test every resource and background path for cross-tenant access.
- [ ] Protect platform-support impersonation with approval and audit.

## Application and API

- [ ] Validate typed inputs and safe file types/sizes.
- [ ] Prevent injection, IDOR, mass assignment, SSRF, and unsafe deserialisation.
- [ ] Add rate limits, timeouts, body limits, secure headers, and CORS policy.
- [ ] Use opaque identifiers where appropriate; never rely on opacity as access control.
- [ ] Implement idempotency for writes and replay protection for webhooks.
- [x] Redact structured credential fields and common credentials in messages/exceptions.
- [x] Add negative tests for credential-field, message, URL, bearer, and exception redaction.
- [x] Add trusted-host validation and baseline secure response headers.

## Data and cryptography

- [ ] TLS in transit and approved encryption at rest.
- [ ] Central secret manager with rotation and no committed secrets.
- [ ] Restricted database roles; evaluate row-level security.
- [ ] Encrypt especially sensitive fields where threat model requires it.
- [ ] Tenant-aware cache, object-store, search, analytics, and backup isolation.
- [ ] Tested backup/restore, retention, deletion, and key-rotation procedures.

## ERP integrations

- [ ] Read-only credentials by default and scoped per tenant/connector.
- [ ] Separate restricted write-back credentials.
- [ ] Verify webhook signatures and reject replay.
- [ ] Quarantine invalid/untrusted payloads.
- [ ] Require confirmation for consequential write-back.
- [ ] Audit requests/responses safely without leaking secrets or excess PII.

## AI and ML

- [x] Separate generative AI from authoritative calculations and access control.
- [ ] Authorise retrieval per user, role, tenant, document, and policy version.
- [ ] Defend against prompt injection and untrusted document instructions.
- [ ] Ground responses, provide citations, validate output, and support abstention.
- [ ] Prevent model/provider logging or training on sensitive data unless approved.
- [ ] Version prompts/models/rules and evaluate leakage, bias, hallucination, and drift.
- [ ] Require human approval for consequential actions.

## Supply chain and operations

- [ ] Pin dependencies and generate an SBOM.
- [ ] Run secret, dependency, SAST, container, IaC, and DAST scans.
- [x] Configure secret, dependency, SAST, SBOM, container-scan, and container-smoke CI gates.
- [ ] Sign/verify build artifacts and protect CI credentials.
- [ ] Centralise immutable audit events with monitored access.
- [ ] Define alerts, incident response, evidence preservation, and breach procedures.
- [ ] Test rate-limit, denial-of-service, failover, disaster recovery, and rollback.

## Phase 1 security status

Phase 1 adds a small operational API attack surface. It includes trusted-host checks,
request-ID validation, no-store/no-sniff/frame/referrer headers, generic internal
errors, production fail-fast settings, structured logs, and message/exception
redaction. A direct secret-log probe passes. The complete security suite is present
but has not executed because dependency retrieval is blocked. Authentication and tenant
isolation are intentionally deferred because no business data or business endpoint
exists; they become mandatory in Phase 2.
