# Evidence ledger and gates

## Evidence precedence

1. Signed/checksum-bound package with named approvals.
2. Source-side evidence for the named version/environment.
3. Approved architecture, privacy, security and operational policies.
4. Executable schemas, mappings, migrations and tests.
5. Narrative documents.
6. Generated examples.
7. Assumptions and verbal statements.

Never let a lower tier silently override a higher tier. Record conflicts.

## Ledger columns

Record identifier, version, owner, evidence path, checksum/approval id, scope,
status, conflicts, expiry/review date and affected artifacts.

## Gates

- Discovery complete: source identity, inventory, transport candidate, owners, scope
  and exclusions exist.
- Concrete design ready: schemas/examples, exhaustive dispositions, authority,
  identity, transport/network/credential, privacy, numeric gates and approvals exist.
- Design approved: all artifacts agree on exact versions/scope and independent review
  has no unresolved high finding.
- Implementation accepted: additive migration, vertical tests, tenant/RLS, transport
  security, recovery, reconciliation, rights/retention and every quality/runtime gate pass.
- Production enablement: deployment approvals, provisioned secrets/network, source
  read-only proof, recovery, monitoring, rollback and data-protection sign-off pass.

Implementation acceptance never implies production enablement.

## Conflict scan

Search all artifacts for package/vendor/product/version, adapter, transport, schema,
mapping, authority, identity, privacy and threshold versions, retention, numeric gates,
events, migration head, statuses and approval names. Resolve every stale/conflicting
value before approval.
