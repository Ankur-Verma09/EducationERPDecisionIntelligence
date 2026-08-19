---
name: refine-erp-connector
description: Qualify, design, review, and incrementally refine education ERP connectors from source discovery through production approval. Use when onboarding a vendor ERP; collecting source inventories, schemas, mappings, authority, identity, privacy, transport, credentials, thresholds, or owner approvals; converting a mock connector into a real connector; assessing connector entry criteria; refining connector data or code; generating HLD/LLD/data/API/threat/test artifacts; or deciding whether implementation or production enablement is authorized.
---

# Refine ERP Connector

Use an evidence-first, fail-closed workflow. Never turn examples, guesses, demo values,
or vendor marketing claims into production authority.

## Workflow

1. Locate governance, canonical schemas, connector code/tests, and supplied source
   packages. Preserve uncommitted work and phase boundaries.
2. Classify the request as discovery, structural design, concrete design,
   implementation, validation, or production enablement. Do not infer a later stage.
3. Read [questions.md](references/questions.md) and ask only unanswered questions for
   the current gate. Prefer evidence files and named approvals over prose answers.
4. Build the ledger in [evidence-and-gates.md](references/evidence-and-gates.md). Mark
   each item `verified`, `conflicting`, `missing`, or `not-applicable` with reason.
5. Validate a package with `scripts/validate_authority_package.py`. Success proves
   structural completeness, not truth or approval.
6. If authority is incomplete, produce a blocked entry assessment and package
   checklist. Refine structural architecture but leave source-specific values unbound.
7. If complete, update HLD, LLD, data model, API/event contract, threat model,
   implementation plan, entry assessment, decisions, risks, status and traceability.
   Use generated or irreversibly anonymised examples only.
8. Independently review design before implementation. Resolve conflicts and re-review.
9. For authorized implementation, follow [code-refinement.md](references/code-refinement.md),
   use small vertical packages, and keep migrations additive and immutable.
10. Run gate-appropriate validation and independently review completion. Keep demo,
    staging, production, real-source, intervention, and AI approvals separate.

## Non-negotiable rules

- ERP facts remain authoritative; canonical projections preserve source lineage.
- Core remains healthy when the connector, source, or AI is unavailable.
- A read-only connector exposes no source mutation path.
- Credentials remain opaque references and never enter APIs, databases, logs, events,
  fixtures, documents, or committed configuration.
- Tenant context is mandatory at API, worker, database, staging, audit and event layers.
- Unknown fields, drift, ambiguous identity, authority conflicts, prohibited child
  attributes and threshold breaches fail closed.
- Checkpoints advance only with committed outcomes, lineage, audit and outbox state.
- Never use real student data in examples, tests, screenshots, prompts or repositories.
- Never begin intervention or AI work as an implied connector task.

## Conclusion language

Use exactly one scoped conclusion:

- `Approved for implementation` only after complete authority and independent review.
- `Accepted structural scaffold; concrete design blocked` when source decisions or
  approvals are missing.
- `Rework required` when evidence conflicts or controls are incomplete.

State what is authorized, prohibited, missing, deferred and the exact next evidence
request. Never say “approved” without its scope.
