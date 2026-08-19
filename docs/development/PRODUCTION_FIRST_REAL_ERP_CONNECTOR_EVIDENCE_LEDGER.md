# Production First Real ERP Connector evidence ledger

Assessment date: 2026-08-05  
Package assessed: `docs/pilot/mock/synthetic_reference_erp_v1`  
Qualification: **Accepted structural scaffold; concrete design blocked**

The package validator returned `blocked`: source release is absent,
`authoritative_for_real_connector` is false, and required production product,
source, privacy and security approvals are absent. Demo values below may inform test
structure but cannot be copied into production authority.

| Evidence item | Version/owner | Evidence | Status | Conflict or downstream effect |
|---|---|---|---|---|
| Package identity and checksums | `synthetic-reference-erp-v1@1.0.0`; demo sponsor | `manifest.json` | Verified for demo | Explicitly non-production; cannot bind a real adapter |
| Real vendor/product/version/edition | None | Fictional `Example Education Systems / Synthetic Reference ERP 1.0` | Missing | Production HLD/registry kind cannot be bound |
| Source release | None | No manifest value | Missing | Schema compatibility and change policy cannot be assessed |
| Tenant and business capability | None | No production scope record | Missing | Purpose, authorization and volume are unbound |
| Scope exclusions | Demo excludes production/write-back/real matching | Manifest prohibited uses | Verified for demo | Production exclusions need owner approval |
| Source inventory/schema | Six generated objects; schema hash present | schema, records and workbook | Verified for demo | Real objects, keys, deletions and extraction semantics missing |
| Field dispositions/mappings | version 1 generated policy | `field_dispositions.json`, workbook | Verified for demo | Must be replaced exhaustively for the real source |
| Source authority/precedence | Mock-primary only | workbook/design narrative | Missing for production | Conflict promotion cannot be approved |
| Identity/correction rules | version 1 exact mock key; no auto-merge | `identity_policy.json` | Verified for demo | Real identifier reuse/merge/split semantics and owner approval missing |
| Read-only transport | in-process CSV test double | `transport_policy.json` | Not applicable to production | Select managed CSV, SFTP, API or read replica |
| Endpoint/network/TLS policy | no network | transport policy | Missing | Destination, port, region and certificate/host-key controls unbound |
| Credential policy/read-only proof | no credential | transport policy | Missing | Secret manager, rotation/revocation and source-side read-only proof required |
| Privacy/lawful purpose | generated demonstration only | `privacy_policy.json` | Conflicting with production need | Jurisdiction, controller instruction and real-data lifecycle absent |
| Prohibited attributes | generated allowlist/reject list | privacy policy/schema | Verified structurally | Production field classifications and privacy approval missing |
| Retention/masking/rights | 24h landing/7d quarantine; mock has no subjects | privacy policy | Missing for production | Canonical/lineage/audit/backup retention and rights flow unbound |
| Numeric quality gates | version 1 mock values | `thresholds.json` | Conflicting with production need | Real baselines, windows, actions and owners missing |
| Operational SLOs | local test bounds only | transport policy | Missing | RPO/RTO, schedule, throughput, lag, monitoring and escalation unbound |
| Product owner approval | `NOT-APPROVED` | manifest | Missing | Blocks concrete design and implementation |
| Source owner approval | `NOT-APPROVED` | manifest | Missing | Blocks schema, mapping and transport authority |
| Privacy owner approval | `NOT-APPROVED` | manifest | Missing | Blocks real child-data processing design |
| Security owner approval | `NOT-APPROVED` | manifest | Missing | Blocks credential/network/TLS design |
| Operations owner approval | None | No approval record | Missing | Blocks support, monitoring and production enablement |
| Example provenance | generated, seeded and checksum-bound | manifest and README | Verified | Safe for demo/tests only |
| Structural design scaffold | independently accepted | production HLD/LLD/data/API/threat/plan review | Verified | May be refined without source-specific binding |
| Implementation authorization | None | governance explicitly blocks it | Missing | No connector code or migration authorized |
| Production enablement authorization | None | governance explicitly blocks it | Missing | No real connection, credentials or activation authorized |

## Unanswered questions for the next gate

### Priority 1 — discovery completion

1. What exact vendor, product, edition, product version and source release will be used?
2. Which institution/tenant and business capability are in scope, and is the target
   pilot, staging, production-read validation or production activation?
3. Who are the named product, ERP/source, privacy, security and operations owners?
4. Which source objects/streams and academic-period range are required?
5. Which single read-only transport is proposed?
6. Which write-back, interventions and AI behavior remain explicitly excluded?

### Priority 2 — concrete design readiness

1. Provide generated or irreversibly anonymised schemas with keys, timestamps,
   deletion markers, null/enum/timezone semantics and incremental/snapshot behavior.
2. Provide exhaustive field dispositions, canonical mappings, authority/precedence,
   correction, conflict, late-arrival and reconciliation rules.
3. Define stable identifiers, reuse/merge/split behavior, normalization and permitted
   human identity decisions.
4. Provide destination/port/path/region plus TLS or host-key policy, source read-only
   proof, secret-manager reference model and rotation/revocation controls.
5. Provide jurisdiction, controller instruction, lawful purpose, field classification,
   masking, all-store retention, legal hold, backup deletion and subject-rights flow.
6. Provide numeric quality gates with scope/window/clock and breach actions, plus
   page/byte/time/concurrency/rate/retry limits and RPO/RTO/monitoring ownership.
7. Bind everything into a checksum- or signature-controlled package with dated named
   product, source, privacy, security and operations approvals.

## Gate decision

- Discovery complete: **No**.
- Concrete design ready: **No**.
- Design approved: **No**; only the structural scaffold is independently accepted.
- Implementation accepted/authorized: **No**.
- Production enablement: **No**.

Next authorized gate: **Discovery and production authority-package completion only**.
Permitted work is collecting, anonymising/generating, validating and reconciling the
missing evidence. Structural documents may be refined. Real transport access,
credential provisioning, source-specific implementation, migration, intervention
workflow and Phase 4 AI work remain prohibited.
