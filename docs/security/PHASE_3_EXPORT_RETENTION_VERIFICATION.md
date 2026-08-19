# Phase 3 Export and Backup Retention Verification

Status: Verified for Phase 3 metadata-only scope  
Evidence date: 2026-07-30

Phase 3 creates no downloadable subject-data artifact and has no object-storage or
backup-export integration. Its export endpoint creates one append-only metadata
manifest per generated subject-rights request, scoped to one tenant and learner, with
a 24-hour expiry. PostgreSQL RLS, MFA, dedicated permission, required reason and
audit apply.

The deployment gate fails if any Phase 3 environment introduces artifact storage,
download URLs, backup exports, or retention beyond manifest expiry without an
approved encryption key, deletion lifecycle, legal-hold behavior, access audit and
restore-time retention test. Such implementation is not authorized in Phase 3.

Verification:

- OpenAPI contains no artifact download or physical-delete operation.
- Manifest responses contain metadata only.
- A second manifest for the same request is rejected.
- `subject_export_manifests` is append-only and tenant-RLS protected.
- Trivy and Gitleaks gates apply to the release image and repository.

All examples and test identifiers are generated.
