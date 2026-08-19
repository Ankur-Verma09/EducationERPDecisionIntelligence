# Synthetic Reference ERP v1 Pilot Package

Classification: **GENERATED TEST DATA — NON-PRODUCTION — NOT SOURCE-OWNER APPROVED**

Approval: **Approved by the user for local/demo use only on 2026-08-05.** Production
use and any real ERP connection remain prohibited.

This replaceable package exercises the Sprint 5 design without claiming to represent
any real ERP. `Synthetic Reference ERP`, vendor `Example Education Systems`, version
`1.0`, and every person/identifier/value in this folder are fictional.

## Replacement contract

Replace this entire version folder with a separately reviewed package. Keep the same
top-level file roles so design and test tooling can compare packages mechanically:

- `manifest.json`: identity, version, classification, checksums and file roles.
- `schemas/`: closed source schemas.
- `data/`: deterministic generated happy-path records.
- `scenarios/`: generated negative/resilience records.
- `policies/`: mock transport, identity, privacy, threshold and machine-verifiable
  source-field disposition policies.
- `pilot_matrices.xlsx`: source inventory, mappings, authority and thresholds.

Mock values must never be copied into production configuration. This package does
not unblock or approve a real ERP connector.

## Synthetic transport profile

The mock assumes a read-only CSV snapshot delivered through an in-process transport
test double. It opens no network connection, uses no credential and reads no local
customer path. A future package must replace this with an approved CSV/SFTP/API/
read-replica contract and deployment policy.
