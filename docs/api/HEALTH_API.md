# Foundation Health API

Base path: `/api/v1`

All responses include `X-Request-ID`. A valid caller-supplied UUID is propagated;
otherwise the API creates one. Responses also set no-store, no-sniff, frame-denial,
and no-referrer headers.

## `GET /health/live`

Confirms that the API process can serve requests. It does not query dependencies.

```json
{"status": "ok"}
```

## `GET /health/ready`

Executes `SELECT 1` and verifies that the database's Alembic revision matches the
application's expected revision.

- `200 {"status":"ok"}` when the database is reachable.
- `503 {"status":"not_ready"}` when it is unavailable, unmigrated, or stale.

Driver or credential details are never returned. These operational endpoints expose
no institution or user data and require no authentication during Phase 1.

The generated OpenAPI document is served at `/openapi.json` when
`EDUERP_DOCS_ENABLED=true`.
