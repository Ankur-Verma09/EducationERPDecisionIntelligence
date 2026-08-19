# Production connector authority package requirements

Create `docs/pilot/production/<vendor_product>/<package-version>/` containing:

- a manifest with immutable package id/version, vendor/product/product version,
  source release, classification, checksums and explicit production scope;
- source inventory and representative irreversibly anonymised schemas/examples;
- exhaustive field-to-canonical dispositions and source-authority matrix;
- stable identity, normalization, ambiguity, correction, precedence and late-arrival rules;
- selected read-only transport contract and source-side read-only proof;
- destination/port/TLS/data-region policy and opaque secret-provider reference model;
- landing/quarantine masking, retention, legal hold, deletion, export and subject-rights rules;
- numeric completeness, freshness, rejection, duplicate, unresolved-reconciliation,
  variance, page/byte/time/concurrency/retry and recovery thresholds;
- named product, source, privacy and security owners with approval identifiers/dates;
- package signature or trusted checksum approval record.

Examples must be generated or irreversibly anonymised. No secret, live endpoint,
student record or copied production payload may be committed.
