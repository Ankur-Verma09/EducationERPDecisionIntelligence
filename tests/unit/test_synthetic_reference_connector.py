from pathlib import Path
from shutil import copytree

import pytest

from education_erp.connectors.synthetic_reference import (
    MANIFEST_SHA256,
    MAX_RECORD_BYTES,
    PACKAGE_ID,
    PACKAGE_VERSION,
    SCENARIOS,
    SyntheticReferenceAdapter,
    package_root,
    verify_package,
)
from education_erp.errors import ApiError


def test_package_is_fixed_checksum_bound_and_demo_only() -> None:
    manifest = verify_package()
    assert manifest["package_id"] == PACKAGE_ID
    assert manifest["package_version"] == PACKAGE_VERSION
    assert manifest["approved_for_demo"] is True
    assert manifest["authoritative_for_real_connector"] is False
    assert manifest["approval_scope"] == "demo-only-non-production"
    assert len(MANIFEST_SHA256) == 64
    assert all(
        value == "NOT-APPROVED"
        for key, value in manifest["approvals"].items()
        if key.startswith("production_")
    )
    assert package_root().name == "synthetic_reference_erp_v1"


def test_valid_adapter_maps_all_entities_without_write_surface() -> None:
    adapter = SyntheticReferenceAdapter("valid")
    first = adapter.read_batch("0", 5)
    second = adapter.read_batch(first.next_checkpoint, 1000)
    records = (*first.records, *second.records)
    assert len(records) == 12
    assert {record.entity_type for record in records} == {
        "academic-period",
        "programme",
        "programme-version",
        "course",
        "course-version",
        "offering",
        "learner",
        "programme-enrolment",
        "offering-enrolment",
    }
    assert second.source_exhausted is True
    assert not hasattr(adapter, "write")
    assert not hasattr(adapter, "delete")
    assert not hasattr(adapter, "request")


@pytest.mark.parametrize("scenario", sorted(SCENARIOS - {"valid"}))
def test_every_approved_scenario_is_closed_and_deterministic(scenario: str) -> None:
    adapter = SyntheticReferenceAdapter(scenario)
    if scenario in {
        "schema-drift-extra-field",
        "transport-timeout",
        "transport-throttled",
        "credential-rejected",
    }:
        with pytest.raises(ApiError):
            adapter.read_batch("0", 100)
    else:
        batch = adapter.read_batch("0", 100)
        assert batch.source_exhausted
        if scenario == "oversized-record":
            assert max(len(str(item.document)) for item in batch.records) > MAX_RECORD_BYTES


def test_adapter_rejects_unknown_scenario_and_checkpoint() -> None:
    with pytest.raises(ApiError):
        SyntheticReferenceAdapter("production")
    with pytest.raises(ApiError):
        SyntheticReferenceAdapter("valid").read_batch("not-an-offset", 10)


def test_package_resolver_has_no_environment_or_caller_path_surface() -> None:
    assert package_root() in {
        Path(__file__).resolve().parents[2] / "docs/pilot/mock/synthetic_reference_erp_v1",
        Path("/app/demo-package"),
    }


def test_manifest_substitution_fails_against_compiled_approval_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import education_erp.connectors.synthetic_reference as module

    copied = tmp_path / "package"
    copytree(package_root(), copied)
    manifest = copied / "manifest.json"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace("1.0.0", "9.9.9", 1))
    monkeypatch.setattr(module, "package_root", lambda: copied)
    with pytest.raises(ApiError) as caught:
        verify_package()
    assert caught.value.code == "package_checksum_mismatch"
