# Connector discovery questions

Ask incrementally and skip questions answered by versioned evidence.

## Business and ownership

1. Which tenant and business capability are in scope?
2. What vendor, product, product version, edition and source release apply?
3. Who are the named product, source, privacy, security and operations owners?
4. What approval identifier and date does each owner provide?
5. Is the goal demo, pilot, staging, production read, or production activation?
6. Which write-back, interventions and AI behaviors are explicitly excluded?

## Source inventory and meaning

1. Which objects, endpoints, views/files and academic periods are required?
2. What are source keys, uniqueness, update timestamps and deletion markers?
3. Is extraction snapshot, incremental, CDC-like, or effective-dated?
4. What timezone, locale, encoding, enum and null semantics apply?
5. Which fields are authoritative, derived, deprecated or unreliable?
6. What source change-notification and compatibility policy exists?
7. Provide generated or irreversibly anonymised schemas and edge cases.

## Mapping, authority and identity

1. What is every field’s disposition: map, transform, reference, quarantine, reject,
   or intentionally ignore?
2. What canonical field and transform version receives each mapped field?
3. Which source outranks another per entity/field and effective interval?
4. How are corrections, reversals, deletions, late arrivals and conflicts handled?
5. What stable identifiers exist, and are they reused, merged, split or reassigned?
6. What normalization is allowed? Which composite matches are exact?
7. Which ambiguity requires reconciliation, and who may approve merge/split?
8. Define observed, source-updated, effective and extraction time semantics.

## Transport, network and credentials

1. Which read-only transport is approved: managed CSV, SFTP, API, or read replica?
2. Which destinations, ports, DNS names, paths/views and regions are allowlisted?
3. What TLS/host-key/certificate verification and rotation rules apply?
4. What evidence proves the source account cannot write or run unsafe queries?
5. Which secret manager owns credentials and what opaque reference is deployable?
6. Define authentication lifetime, rotation, revocation and break-glass rules.
7. Define page/byte/time/concurrency/rate/retry/backoff/jitter/circuit limits.
8. What maintenance windows and source escalation path apply?

## Privacy and child-data controls

1. What jurisdiction, controller instruction and lawful purpose apply?
2. What classification applies to every included field?
3. Which sensitive/prohibited fields must be rejected before persistence?
4. What masking applies to API, UI, logs, events, support and non-production?
5. Define landing, quarantine, canonical, lineage, audit and backup retention.
6. How do access, export, correction, restriction and deletion requests flow?
7. What legal holds and backup deletion exceptions apply?
8. Who may inspect/replay quarantine, with which MFA/reason/audit controls?

## Numeric acceptance and operations

1. Define completeness minimums and freshness, rejection, duplicate, unresolved and
   unexplained-variance maximums.
2. Are gates per stream, entity, tenant, run, period or global?
3. What sample/window and clock define each measurement?
4. Which breach blocks promotion, suspends the connector or only alerts?
5. Define RPO, RTO, throughput, schedule, maximum lag and recovery behavior.
6. Who owns monitoring, incidents, drift and failed reconciliation?

## Approval confirmation

1. Do owners approve the exact package checksum/signature?
2. Are all decisions versioned and mutually consistent?
3. Are examples generated or irreversibly anonymised?
4. Is implementation separately authorized from design approval?
5. Is production enablement separately authorized from implementation acceptance?
