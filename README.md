# Education ERP Decision Intelligence Platform

This repository is the planned home of a secure, multi-tenant decision-intelligence
platform that operates above institutional ERP systems. ERP systems remain the
systems of record.

## Current state

The authoritative Google plan controls phase naming. Existing identity, tenancy,
authorization, canonical education, lineage, reconciliation and privacy work is
credited toward authoritative Phases 1 and 2. Phase 2 remains incomplete until its
connector, mapping, quarantine, watermark, outbox relay and synchronization scope is
implemented. Authoritative Phase 3 (First ERP Connector) is blocked at entry and has
not started.
Phase 4 AI services have not started.

Start with [docs/development/DEVELOPMENT_STATUS.md](docs/development/DEVELOPMENT_STATUS.md).

## Local development

Prerequisites: Python 3.11, Docker Desktop/Engine with Compose, and Make (optional).

```text
python -m venv .venv
.venv\Scripts\python -m pip install -c requirements\constraints.txt -e ".[dev]"
copy .env.example .env
docker compose --profile core up -d --build
```

Compose uses separate migration-owner and least-privileged runtime credentials,
applies migrations, and starts the API. Replace the placeholder values in `.env`
before running the API directly outside Compose.

API documentation is available at `http://localhost:8000/docs`. Run local
non-PostgreSQL validation with:

```text
.venv\Scripts\ruff format --check .
.venv\Scripts\ruff check .
.venv\Scripts\mypy
.venv\Scripts\pytest
```

Local credentials in Compose are development-only and must never be promoted.

Detailed Docker startup, shutdown, validation, and troubleshooting instructions are
available in
[docs/development/DOCKER_VALIDATION_RUNBOOK.md](docs/development/DOCKER_VALIDATION_RUNBOOK.md).
