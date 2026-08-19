import json

import pytest

from education_erp.connectors.operational_validation import PROFILES, report_json, run_profile


@pytest.mark.parametrize("profile", tuple(PROFILES))
def test_operational_profiles_pass_without_claiming_production(profile: str) -> None:
    report = run_profile(profile)  # type: ignore[arg-type]
    assert report["passed"] is True
    assert report["production_ready"] is False
    assert report["network_egress"] is False
    assert report["classification"] == "generated-production-like-validation-only"
    assert report["package"] == "synthetic-reference-erp-v1@1.0.0"


def test_resilience_profile_classifies_closed_failures() -> None:
    report = run_profile("resilience")
    outcomes = {item["scenario"]: item["outcome"] for item in report["results"]}  # type: ignore[union-attr]
    assert outcomes == {
        "schema-drift-extra-field": "source_schema_unsupported",
        "transport-timeout": "transport_unavailable",
        "transport-throttled": "transport_unavailable",
        "credential-rejected": "invalid_connector_config",
    }


def test_soak_profile_workload_is_fixed() -> None:
    report = run_profile("soak")
    result = report["results"][0]  # type: ignore[index]
    assert report["limits"]["batch_size"] == 5  # type: ignore[index]
    assert result["iterations"] == 250
    assert result["records_read"] == 3_000


def test_report_is_safe_machine_readable_generated_evidence() -> None:
    report = json.loads(report_json("baseline"))
    assert report["passed"] is True
    serialized = json.dumps(report)
    assert "credential" not in serialized
    assert "SYN-0001" not in serialized
    assert "source_record" not in serialized
