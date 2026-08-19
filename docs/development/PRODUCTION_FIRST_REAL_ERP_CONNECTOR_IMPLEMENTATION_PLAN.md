# Production First Real ERP Connector implementation plan

Status: **Blocked; planning sequence only; no implementation approval.**

After concrete design approval, execute small vertical packages:

1. Freeze and validate the signed/checksum-bound production authority package.
2. Add the closed transport adapter and deployment connection-profile contract.
3. Add credential injection, destination allowlisting and read-only probe evidence.
4. Add a self-contained additive migration after `0008`; never modify `0001`–`0008`.
5. Persist immutable package/schema/mapping/authority/identity/privacy/threshold snapshots.
6. Implement one bounded source stream through staging, validation and canonical observation.
7. Add identity, precedence, late-arrival, quarantine, rights and retention handling.
8. Add reconciliation gates, safe events and operational suspension/recovery.
9. Add unit, PostgreSQL, API, security, transport resilience and end-to-end tests.
10. Run quality, migration, image, SBOM, dependency, Trivy, Gitleaks and smoke gates.
11. Update governance and independently review completion before production enablement.

Work-package estimates and migration shape remain unset until package scale, transport,
schema and operational SLOs are authoritative.
