# Production First Real ERP Connector API and event contract

Status: **Blocked — transport and package-specific schemas are absent.**

Existing tenant authorization, hidden-404 behavior, MFA, reason, ETag, opaque cursor
and persistent idempotency controls remain mandatory. A production connector create
request may contain only an approved package id/version, display name and an opaque
deployment connection-profile id. It must not accept raw endpoints, SQL, filesystem
paths, credentials, TLS-disable flags, arbitrary mappings or arbitrary configuration.

Required operations are create-disabled, test/probe, dry-run, activate, suspend,
start/cancel sync, job/run/reconciliation/quarantine reads and approved replay. Probe,
dry-run and activation contracts cannot be frozen before the transport is named.

Events retain tenant, event, aggregate, trace, correlation, causation, occurrence and
schema-version metadata. Required event families cover probe, schema drift, sync,
batch validation, reconciliation/threshold breach, credential rotation requirement,
suspension and terminal failure. Payloads contain no source values, learner keys,
credentials, endpoints or sensitive exception text.
