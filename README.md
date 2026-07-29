# Education ERP Decision Intelligence Platform

This repository is the planned home of a secure, multi-tenant decision-intelligence
platform that operates above institutional ERP systems. ERP systems remain the
systems of record.

## Current state

Phase 1 foundation implementation and its local acceptance gates are complete.
No Phase 2 identity or tenancy functionality has been implemented.

Start with [docs/development/DEVELOPMENT_STATUS.md](docs/development/DEVELOPMENT_STATUS.md).

## Local development

Prerequisites: Python 3.11, Docker Desktop/Engine with Compose, and Make (optional).

```text
python -m venv .venv
.venv\Scripts\python -m pip install -c requirements\constraints.txt -e ".[dev]"
copy .env.example .env
docker compose up -d database
.venv\Scripts\alembic upgrade head
.venv\Scripts\uvicorn education_erp.main:app --reload
```

API documentation is available at `http://localhost:8000/docs`. Run validation with:

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
