"""Validate the replaceable generated Sprint 5 pilot package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

# ruff: noqa: S101 -- assertions intentionally fail this deterministic package validator.


ROOT = Path("docs/pilot/mock/synthetic_reference_erp_v1")


def load_json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    manifest = load_json("manifest.json")
    assert manifest["classification"] == "generated-test-data-non-production"
    assert manifest["authoritative_for_real_connector"] is False
    assert manifest["approved_for_demo"] is True
    assert manifest["approval_scope"] == "demo-only-non-production"
    assert manifest["approvals"]["demo_sponsor"] == "USER-APPROVED-2026-08-05"
    assert all(
        value == "NOT-APPROVED"
        for key, value in manifest["approvals"].items()
        if key.startswith("production_")
    )

    for relative, expected in manifest["sha256"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()
        assert actual == expected, f"checksum mismatch: {relative}"

    records = load_json("data/valid_records.json")
    assert sum(len(rows) for rows in records.values()) == 8
    assert {row["institution_reference"] for row in records["learners"]} == {
        "SYN-0001",
        "SYN-0002",
    }
    serialized = json.dumps(records).lower()
    for prohibited in ("date_of_birth", "health", "religion", "ethnicity", "email", "phone"):
        assert prohibited not in serialized

    thresholds = load_json("policies/thresholds.json")
    assert thresholds["classification"] == "mock-only-not-production-authority"
    assert thresholds["promotion_on_breach"] == "blocked"

    transport = load_json("policies/transport_policy.json")
    assert transport["network_egress"] == "disabled"
    assert transport["credential_reference"] is None
    assert not set(transport["allowed_operations"]) & set(transport["forbidden_operations"])

    schema = load_json("schemas/source_bundle.schema.json")
    dispositions = load_json("policies/field_dispositions.json")
    schema_refs = {
        "academic_periods": "academic_period",
        "programmes": "programme",
        "courses": "course",
        "offerings": "offering",
        "learners": "learner",
        "enrolments": "enrolment",
    }
    for source_object, definition in schema_refs.items():
        required_fields = set(schema["$defs"][definition]["required"])
        assert set(dispositions["objects"][source_object]) == required_fields
    expected_multi_target = {
        "enrolments.enrolment_id": [
            "programme-enrolment.source_record_key",
            "offering-enrolment.source_record_key",
        ],
        "enrolments.effective_from": [
            "programme-enrolment.effective_from",
            "offering-enrolment.effective_from",
        ],
        "enrolments.status": [
            "programme-enrolment.status",
            "offering-enrolment.status",
        ],
    }
    assert dispositions["required_multi_target_dispositions"] == expected_multi_target

    scenarios = load_json("scenarios/negative_scenarios.json")["scenarios"]
    required = {
        "schema-drift-extra-field",
        "prohibited-child-attribute",
        "duplicate-version",
        "ambiguous-identity",
        "late-correction",
        "transport-timeout",
        "transport-throttled",
        "credential-rejected",
        "oversized-record",
    }
    assert {item["id"] for item in scenarios} == required
    print("synthetic-reference-erp-v1: valid")


if __name__ == "__main__":
    main()
