# Code and data refinement

## Vertical sequence

1. Package validator and immutable registry binding.
2. Read-only transport probe and network/credential controls.
3. One bounded source stream through staging.
4. Closed schema validation and prohibited-field rejection.
5. One canonical projection with lineage and authority.
6. Durable checkpoint, replay and kill/resume behavior.
7. Reconciliation and promotion gates.
8. Quarantine, retention, masking and subject rights.
9. Safe APIs/events, suspension and observability.
10. Remaining streams, each repeating the controls/tests.

## Data refinement

- Diff schemas; never auto-accept additive fields.
- Require a disposition for every source field and source for every required target.
- Version transforms; forbid arbitrary code/SQL in mappings.
- Retain source keys only when approved; otherwise tenant-locally fingerprint them.
- Test nulls, enums, Unicode, timezones, reused IDs, late events, deletes, conflicts,
  size abuse and prohibited fields with generated fixtures.

## Code refinement

- Keep adapters separate from canonical DB sessions.
- Keep endpoint/path/query/credential selection out of request-controlled input.
- Use typed closed models and safe error codes.
- Persist failure state instead of rolling it back with extraction failure.
- Bound attempts, concurrency, memory, page, record and batch sizes.
- Commit checkpoint, outcomes, lineage, audit and outbox atomically.
- Enforce tenant isolation in application and PostgreSQL using a non-bypass role.
- Keep migrations self-contained/additive and checksum-baseline them after acceptance.

## Minimum tests per stream

Happy path; replay; restart before/after commit; cross-tenant API/RLS; drift;
prohibited/oversized fields; identity ambiguity; precedence conflict; late correction;
deletion marker; timeout; throttling; credential and TLS failure; SSRF rejection;
threshold breach; retention bound; quarantine authorization; leakage; Core outage isolation.
