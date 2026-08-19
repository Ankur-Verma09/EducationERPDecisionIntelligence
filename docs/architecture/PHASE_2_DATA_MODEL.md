# Phase 2 Data Model

Status: Approved baseline  
Date: 2026-07-29

All identifiers are UUIDs. All timestamps are timezone-aware UTC. Mutable aggregates
include `version`, `created_at`, and `updated_at`. Tenant-owned tables use forced RLS.

## Entities

### `institutions`

- `id` — tenant identifier
- `slug` — globally unique, immutable, never reused
- `legal_name`
- `display_name`
- `status`
- `data_region`
- `security_epoch`
- `deletion_requested_at`
- lifecycle/version timestamps

The institution registry is control-plane data. Tenant reads of their own row are
permitted; cross-tenant platform operations use dedicated control-plane policy.

### `campuses`

- `id`, `tenant_id`
- `code`, `name`, `status`
- tenant-scoped unique `(tenant_id, code)`

### `departments`

- `id`, `tenant_id`, `campus_id`
- `code`, `name`, `status`
- composite foreign key `(tenant_id, campus_id)`
- tenant-scoped unique `(tenant_id, campus_id, code)`

### `users`

- `id`
- `status`
- `display_name`
- `work_email_normalized`
- `security_epoch`
- `last_authenticated_at`

Users are platform identity records. They contain no password or tenant-derived
authorization.

### `external_identities`

- `id`, `user_id`
- `issuer`, `subject`
- `email_at_link_time`
- `linked_at`, `last_seen_at`
- unique `(issuer, subject)`

### `memberships`

- `id`, `tenant_id`, `user_id`
- `status`
- `invited_by_user_id`, `invited_at`, `activated_at`, `revoked_at`
- `security_epoch`
- unique active membership `(tenant_id, user_id)`

### `roles`

- `id`
- `name`
- `description`
- `is_builtin`
- `risk_level`

Built-in Phase 2 roles are defined in the approved security model.

### `permissions`

- `id`
- `name` — globally unique `resource:action`
- `description`
- `risk_level`
- `requires_mfa`
- `requires_recent_auth`

### `role_permissions`

- `role_id`, `permission_id`
- immutable for built-in roles through application APIs

### `role_assignments`

- `id`, `tenant_id`, `membership_id`, `role_id`
- optional `campus_id`, optional `department_id`
- `granted_by_user_id`, `granted_at`, `expires_at`, `revoked_at`
- tenant-consistent composite foreign keys
- partial uniqueness preventing duplicate active assignments

### `tenant_security_policies`

- `tenant_id`
- `mfa_required_for_all`
- `session_max_minutes`
- `allowed_email_domains`
- `version`, timestamps

Values cannot weaken the platform minimums.

### `support_access_grants`

- `id`, `tenant_id`, `support_user_id`
- `reason`, `ticket_reference`
- `scope`
- `requested_at`, `approved_by_user_id`, `approved_at`
- `starts_at`, `expires_at`, `revoked_at`
- `is_break_glass`, `reviewed_at`

Maximum duration is policy constrained. Grants cannot create role assignments.

### `idempotency_records`

- `id`
- `scope_type`, `scope_id`
- `actor_user_id`, `method`, `route`, `key`
- `request_hash`
- response status/body reference
- `created_at`, `expires_at`
- unique scoped key

### `audit_events`

- `id`, `occurred_at`
- optional `tenant_id`
- `actor_user_id`, `actor_issuer`, `actor_subject`
- `action`, `target_type`, optional `target_id`
- `outcome`, `request_id`
- `authentication_assurance`
- optional `reason`, `ticket_reference`
- minimised JSON `changes`
- integrity sequence/hash fields reserved for tamper-evidence

No update/delete grants are provided to runtime roles.

## Relationship rules

- Campus and department always share the institution tenant.
- Membership joins a platform user to one institution.
- Role assignment always references a membership in the same tenant.
- Scoped assignment campus/department must belong to the same tenant.
- Audit events for tenant operations carry the same tenant.
- No Phase 2 table stores student, academic, attendance, fee, health, disciplinary,
  guardian, or risk data.

## RLS policy shape

Tenant-owned tables use policies equivalent to:

```sql
USING (
  tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
)
WITH CHECK (
  tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
)
```

Tables enable and force RLS. Control-plane access is implemented separately and
cannot be reached by tenant endpoints.

## Migration requirements

- One schema-bearing Phase 2 migration series with reversible ordering.
- Create runtime and migration role expectations in deployment documentation; do not
  embed credentials.
- Seed built-in roles/permissions deterministically and idempotently.
- Enable/force RLS after tables and policies exist.
- Downgrade must remove policies before tables.
- Test upgrade/downgrade/upgrade and fresh versus populated upgrade.
