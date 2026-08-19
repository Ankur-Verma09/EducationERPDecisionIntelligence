"""Synthetic-only operational validation for the generated demo connector."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Literal

from education_erp.connectors.synthetic_reference import (
    PACKAGE_ID,
    PACKAGE_VERSION,
    PAGE_SIZE,
    SyntheticReferenceAdapter,
    verify_package,
)
from education_erp.errors import ApiError

ProfileName = Literal["baseline", "resilience", "soak"]


@dataclass(frozen=True)
class OperationalProfile:
    name: ProfileName
    valid_iterations: int
    batch_size: int
    scenarios: tuple[str, ...]
    max_valid_run_ms: float


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    iterations: int
    records_read: int
    duration_ms: float
    outcome: str


PROFILES: dict[ProfileName, OperationalProfile] = {
    "baseline": OperationalProfile("baseline", 10, PAGE_SIZE, ("valid",), 1_000.0),
    "resilience": OperationalProfile(
        "resilience",
        1,
        PAGE_SIZE,
        (
            "schema-drift-extra-field",
            "transport-timeout",
            "transport-throttled",
            "credential-rejected",
        ),
        1_000.0,
    ),
    "soak": OperationalProfile("soak", 250, 5, ("valid",), 5_000.0),
}

EXPECTED_FAILURES = {
    "schema-drift-extra-field": "source_schema_unsupported",
    "transport-timeout": "transport_unavailable",
    "transport-throttled": "transport_unavailable",
    "credential-rejected": "invalid_connector_config",
}


def _read_all(scenario: str, batch_size: int) -> int:
    adapter = SyntheticReferenceAdapter(scenario)
    checkpoint = "0"
    count = 0
    while True:
        batch = adapter.read_batch(checkpoint, batch_size)
        count += len(batch.records)
        if batch.source_exhausted:
            return count
        checkpoint = batch.next_checkpoint


def run_profile(name: ProfileName) -> dict[str, object]:
    """Run a bounded profile and return safe, generated-only evidence."""

    profile = PROFILES[name]
    verify_package()
    results: list[ScenarioResult] = []
    passed = True
    for scenario in profile.scenarios:
        iterations = profile.valid_iterations if scenario == "valid" else 1
        started = perf_counter()
        records = 0
        outcome = "completed"
        try:
            for _ in range(iterations):
                records += _read_all(scenario, profile.batch_size)
        except ApiError as exc:
            outcome = exc.code
        duration_ms = round((perf_counter() - started) * 1_000, 3)
        expected = EXPECTED_FAILURES.get(scenario, "completed")
        if outcome != expected or (scenario == "valid" and duration_ms > profile.max_valid_run_ms):
            passed = False
        results.append(ScenarioResult(scenario, iterations, records, duration_ms, outcome))
    return {
        "contract_version": "1",
        "profile": profile.name,
        "package": f"{PACKAGE_ID}@{PACKAGE_VERSION}",
        "classification": "generated-production-like-validation-only",
        "production_ready": False,
        "network_egress": False,
        "passed": passed,
        "limits": {
            "batch_size": profile.batch_size,
            "max_valid_run_ms": profile.max_valid_run_ms,
        },
        "results": [asdict(result) for result in results],
    }


def report_json(name: ProfileName) -> str:
    return json.dumps(run_profile(name), indent=2, sort_keys=True)
