.PHONY: install run format lint type test security sbom check migrate

install:
	python -m pip install -c requirements/constraints.txt -e ".[dev]"

run:
	uvicorn education_erp.main:app --reload

format:
	ruff format .
	ruff check --fix .

lint:
	ruff format --check .
	ruff check .

type:
	mypy

test:
	pytest

security:
	bandit -c pyproject.toml -r src
	pip-audit

sbom:
	cyclonedx-py environment --output-format JSON --output-file sbom.json

check: lint type test security

migrate:
	alembic upgrade head
